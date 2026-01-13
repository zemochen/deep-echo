"""
Audio transcriber module for real-time speech-to-text conversion.

This module provides improved architecture for audio transcription with better
transcript management, threading, and proper audio source distinction.
"""

import wave
import os
import time
import threading
import tempfile
import queue
import io
from datetime import timedelta, datetime
from heapq import merge
from typing import Dict, List, Tuple, Optional, Callable, Any
import custom_speech_recognition as sr
import pyaudio

from src.utils.logger import get_logger
from src.utils.exceptions import AudioTranscriptionError
from src.utils.retry import retry_with_backoff, RetryConfig
from src.utils.error_recovery import error_tracker, resource_cleanup_manager
from src.audio.models import BaseTranscriber, TranscriptionMode, LanguageDetectionResult

# Constants
PHRASE_TIMEOUT = 3.05
MAX_PHRASES = 10
PROCESSING_INTERVAL = 0.1

logger = get_logger(__name__)


class AudioTranscriber:
    """
    Audio transcriber that converts speech to text in real-time.
    
    This class handles audio processing from microphone and speaker sources,
    manages transcription history, and provides thread-safe access to results.
    """
    
    def __init__(self, mic_source: sr.Microphone, speaker_source: sr.Microphone, model: BaseTranscriber):
        """
        Initialize the audio transcriber.
        
        Args:
            mic_source: Microphone audio source
            speaker_source: Speaker audio source  
            model: Speech recognition model implementing BaseTranscriber interface
        """
        # Initialize transcript data storage
        self.transcript_data: Dict[str, List[Tuple[str, datetime]]] = {
            "You": [], 
            "Speaker": []
        }
        
        # Event to signal transcript changes
        self.transcript_changed_event = threading.Event()
        
        # Audio model for transcription
        self.audio_model = model
        
        # Audio source configurations
        self.audio_sources = {
            "You": {
                "sample_rate": mic_source.SAMPLE_RATE,
                "sample_width": mic_source.SAMPLE_WIDTH,
                "channels": mic_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self._process_mic_data
            },
            "Speaker": {
                "sample_rate": speaker_source.SAMPLE_RATE,
                "sample_width": speaker_source.SAMPLE_WIDTH,
                "channels": speaker_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self._process_speaker_data
            }
        }
        
        # Thread safety lock
        self._lock = threading.RLock()
        
        # Processing state
        self._is_running = False
        self._processing_thread = None
        
        # Register cleanup handlers for resource management
        resource_cleanup_manager.register_cleanup_handler(self._cleanup_temp_files)
        resource_cleanup_manager.register_resource_monitor("transcriber_queues", self._get_queue_metrics)
        
        logger.info("AudioTranscriber initialized successfully")
    
    def start_transcription(self, speaker_queue: queue.Queue, mic_queue: queue.Queue) -> None:
        """
        Start the transcription processing in a background thread.
        
        Args:
            speaker_queue: Queue containing speaker audio data
            mic_queue: Queue containing microphone audio data
        """
        if self._is_running:
            logger.warning("Transcription already running")
            return
            
        self._is_running = True
        self._processing_thread = threading.Thread(
            target=self._transcribe_audio_queue,
            args=(speaker_queue, mic_queue),
            daemon=True,
            name="AudioTranscriber"
        )
        self._processing_thread.start()
        logger.info("Audio transcription started")
    
    def stop_transcription(self) -> None:
        """Stop the transcription processing."""
        self._is_running = False
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=1.0)
        logger.info("Audio transcription stopped")
    
    def _transcribe_audio_queue(self, speaker_queue: queue.Queue, mic_queue: queue.Queue) -> None:
        """
        Main transcription loop that processes audio queues.
        
        Args:
            speaker_queue: Queue containing speaker audio data
            mic_queue: Queue containing microphone audio data
        """
        logger.info("Starting audio transcription processing loop")
        
        while self._is_running:
            try:
                pending_transcriptions = []
                
                # Process microphone data
                mic_data = self._drain_queue(mic_queue)
                if mic_data:
                    transcription = self._process_audio_source("You", mic_data)
                    if transcription:
                        pending_transcriptions.append(transcription)
                
                # Process speaker data
                speaker_data = self._drain_queue(speaker_queue)
                if speaker_data:
                    transcription = self._process_audio_source("Speaker", speaker_data)
                    if transcription:
                        pending_transcriptions.append(transcription)
                
                # Update transcripts in chronological order
                if pending_transcriptions:
                    pending_transcriptions.sort(key=lambda x: x[2])  # Sort by timestamp
                    for who_spoke, text, time_spoken in pending_transcriptions:
                        self.update_transcript(who_spoke, text, time_spoken)
                    
                    self.transcript_changed_event.set()
                
                # Brief pause to prevent excessive CPU usage
                threading.Event().wait(PROCESSING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in transcription loop: {e}")
                # Continue processing despite errors
    
    def _drain_queue(self, audio_queue: queue.Queue) -> List[Tuple[bytes, datetime]]:
        """
        Drain all available data from an audio queue.
        
        Args:
            audio_queue: Queue to drain
            
        Returns:
            List of (audio_data, timestamp) tuples
        """
        data = []
        while True:
            try:
                item = audio_queue.get_nowait()
                data.append(item)
            except queue.Empty:
                break
        return data
    
    @retry_with_backoff(
        exceptions=(AudioTranscriptionError, OSError, IOError),
        config=RetryConfig(max_attempts=2, base_delay=0.5, backoff_factor=1.5)
    )
    def _process_audio_source(self, source_name: str, audio_data: List[Tuple[bytes, datetime]]) -> Optional[Tuple[str, str, datetime]]:
        """
        Process audio data from a specific source.
        
        Args:
            source_name: Name of the audio source ("You" or "Speaker")
            audio_data: List of (audio_data, timestamp) tuples
            
        Returns:
            Tuple of (who_spoke, text, timestamp) or None if no valid transcription
        """
        if not audio_data:
            return None
            
        source_info = self.audio_sources[source_name]
        
        # Update last sample and phrase status
        for data, time_spoken in audio_data:
            self._update_last_sample_and_phrase_status(source_name, data, time_spoken)
        
        # Create temporary file for transcription
        temp_file_path = None
        try:
            fd, temp_file_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            
            # Process audio data to file
            source_info["process_data_func"](source_info["last_sample"], temp_file_path)
            
            # Get transcription
            text = self.audio_model.get_transcription(temp_file_path)
            
            # Filter out empty or invalid transcriptions
            if text and text.strip() and text.lower() != 'you':
                latest_time = max(time for _, time in audio_data)
                return (source_name, text.strip(), latest_time)
                
        except Exception as e:
            error = AudioTranscriptionError(f"Failed to transcribe {source_name} audio: {e}")
            error_tracker.record_error(error, f"transcriber_{source_name.lower()}")
            logger.error(f"Transcription error for {source_name}: {e}")
            raise error
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except OSError as e:
                    logger.warning(f"Failed to cleanup temp file {temp_file_path}: {e}")
        
        return None
    
    def _update_last_sample_and_phrase_status(self, who_spoke: str, data: bytes, time_spoken: datetime) -> None:
        """
        Update the last sample and phrase status for an audio source.
        
        Args:
            who_spoke: Source identifier ("You" or "Speaker")
            data: Audio data bytes
            time_spoken: Timestamp when audio was captured
        """
        source_info = self.audio_sources[who_spoke]
        
        # Check if this is a new phrase based on timeout
        if (source_info["last_spoken"] and 
            time_spoken - source_info["last_spoken"] > timedelta(seconds=PHRASE_TIMEOUT)):
            source_info["last_sample"] = bytes()
            source_info["new_phrase"] = True
        else:
            source_info["new_phrase"] = False
        
        # Accumulate audio data
        source_info["last_sample"] += data
        source_info["last_spoken"] = time_spoken
    
    def _process_mic_data(self, data: bytes, temp_file_name: str) -> None:
        """
        Process microphone audio data and save to temporary file.
        
        Args:
            data: Raw audio data
            temp_file_name: Path to temporary file
        """
        try:
            audio_data = sr.AudioData(
                data, 
                self.audio_sources["You"]["sample_rate"],
                self.audio_sources["You"]["sample_width"]
            )
            wav_data = io.BytesIO(audio_data.get_wav_data())
            with open(temp_file_name, 'w+b') as f:
                f.write(wav_data.read())
        except Exception as e:
            logger.error(f"Error processing microphone data: {e}")
            raise AudioTranscriptionError(f"Failed to process microphone data: {e}")
    
    def _process_speaker_data(self, data: bytes, temp_file_name: str) -> None:
        """
        Process speaker audio data and save to temporary file.
        
        Args:
            data: Raw audio data
            temp_file_name: Path to temporary file
        """
        try:
            with wave.open(temp_file_name, 'wb') as wf:
                wf.setnchannels(self.audio_sources["Speaker"]["channels"])
                p = pyaudio.PyAudio()
                try:
                    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.audio_sources["Speaker"]["sample_rate"])
                    wf.writeframes(data)
                finally:
                    p.terminate()
        except Exception as e:
            logger.error(f"Error processing speaker data: {e}")
            raise AudioTranscriptionError(f"Failed to process speaker data: {e}")
    
    def update_transcript(self, who_spoke: str, text: str, time_spoken: datetime) -> None:
        """
        Update the transcript with new text.
        
        Args:
            who_spoke: Source identifier ("You" or "Speaker")
            text: Transcribed text
            time_spoken: Timestamp when text was spoken
        """
        with self._lock:
            source_info = self.audio_sources[who_spoke]
            transcript = self.transcript_data[who_spoke]
            
            # Log the transcription
            self._log_record(who_spoke, text)
            
            # Format the transcript entry
            formatted_text = f"{who_spoke}: [{text}]\n\n"
            
            if source_info["new_phrase"] or len(transcript) == 0:
                # New phrase - add as new entry
                if len(transcript) >= MAX_PHRASES:
                    transcript.pop(-1)  # Remove oldest entry
                transcript.insert(0, (formatted_text, time_spoken))
            else:
                # Continue existing phrase - update most recent entry
                transcript[0] = (formatted_text, time_spoken)
            
            logger.debug(f"Updated transcript for {who_spoke}: {text[:50]}...")
    
    def get_transcript(self) -> str:
        """
        Get the combined transcript from all sources.
        
        Returns:
            Combined transcript text
        """
        with self._lock:
            # Merge transcripts from both sources, sorted by timestamp (newest first)
            combined_transcript = list(merge(
                self.transcript_data["You"], 
                self.transcript_data["Speaker"],
                key=lambda x: x[1], 
                reverse=True
            ))
            
            # Limit to maximum phrases
            combined_transcript = combined_transcript[:MAX_PHRASES]
            
            # Return just the text portions
            return "".join([entry[0] for entry in combined_transcript])
    
    def get_speaker_transcript(self) -> List[Tuple[str, datetime]]:
        """
        Get the speaker-only transcript.
        
        Returns:
            List of (text, timestamp) tuples for speaker
        """
        with self._lock:
            return self.transcript_data["Speaker"].copy()
    
    def get_speaker_newest(self, last_time: datetime) -> Tuple[datetime, str]:
        """
        Get new speaker messages since the given timestamp.
        
        Args:
            last_time: Timestamp to check for new messages after
            
        Returns:
            Tuple of (latest_timestamp, new_messages_text)
        """
        with self._lock:
            transcript = self.get_speaker_transcript()
            if not transcript:
                return last_time, ""
            
            new_messages = []
            latest_time = last_time
            
            for message, timestamp in transcript:
                if timestamp <= last_time:
                    break
                new_messages.append(message)
                latest_time = max(latest_time, timestamp)
            
            return latest_time, "".join(reversed(new_messages))
    
    def get_mic_transcript(self) -> List[Tuple[str, datetime]]:
        """
        Get the microphone-only transcript.
        
        Returns:
            List of (text, timestamp) tuples for microphone
        """
        with self._lock:
            return self.transcript_data["You"].copy()
    
    def clear_transcript_data(self) -> None:
        """Clear all transcript data and reset audio sources."""
        with self._lock:
            # Clear transcript data
            self.transcript_data["You"].clear()
            self.transcript_data["Speaker"].clear()
            
            # Reset audio source states
            for source_name in ["You", "Speaker"]:
                source_info = self.audio_sources[source_name]
                source_info["last_sample"] = bytes()
                source_info["new_phrase"] = True
                source_info["last_spoken"] = None
            
            logger.info("Transcript data cleared")
    
    def _log_record(self, who_spoke: str, text: str) -> None:
        """
        Log transcript record to file.
        
        Args:
            who_spoke: Source identifier
            text: Transcribed text
        """
        try:
            current_date = datetime.now()
            formatted_date = current_date.strftime('%Y%m%d')
            
            # Ensure log directory exists
            log_dir = "./transcript_log"
            os.makedirs(log_dir, exist_ok=True)
            
            file_name = f"{log_dir}/transcript_{formatted_date}.txt"
            with open(file_name, 'a', encoding='utf-8') as file:
                file.write(f"{who_spoke}: [{text}]\n")
        except Exception as e:
            logger.warning(f"Failed to log transcript record: {e}")
    
    def get_audio_source_info(self, source_name: str) -> Dict[str, Any]:
        """
        Get audio source information for debugging.
        
        Args:
            source_name: Source identifier ("You" or "Speaker")
            
        Returns:
            Dictionary containing source information
        """
        with self._lock:
            if source_name not in self.audio_sources:
                raise ValueError(f"Unknown audio source: {source_name}")
            
            source_info = self.audio_sources[source_name].copy()
            # Remove the function reference for serialization
            source_info.pop("process_data_func", None)
            return source_info
    
    def get_transcription_mode(self) -> TranscriptionMode:
        """
        Get the current transcription mode.
        
        Returns:
            Current TranscriptionMode
        """
        return self.audio_model.get_mode()
    
    def supports_language_detection(self) -> bool:
        """
        Check if the current model supports language detection.
        
        Returns:
            True if language detection is supported
        """
        return self.audio_model.supports_language_detection()
    
    def detect_language_from_audio(self, audio_file_path: str) -> Optional[LanguageDetectionResult]:
        """
        Detect language from an audio file using the current model.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            LanguageDetectionResult if detection is supported and successful
        """
        try:
            return self.audio_model.detect_language(audio_file_path)
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return None
    
    def switch_transcription_model(self, new_model: BaseTranscriber) -> bool:
        """
        Switch to a new transcription model.
        
        Args:
            new_model: New BaseTranscriber instance
            
        Returns:
            True if switch was successful
        """
        try:
            old_mode = self.audio_model.get_mode()
            self.audio_model = new_model
            new_mode = new_model.get_mode()
            
            logger.info(f"Switched transcription model from {old_mode.value} to {new_mode.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch transcription model: {e}")
            return False
    
    def validate_model_consistency(self, expected_mode: TranscriptionMode) -> bool:
        """
        Validate that current model matches expected transcription mode.
        
        Args:
            expected_mode: Expected transcription mode
            
        Returns:
            True if modes are consistent
        """
        actual_mode = self.audio_model.get_mode()
        is_consistent = actual_mode == expected_mode
        
        if not is_consistent:
            logger.warning(f"Model mode inconsistency: expected {expected_mode.value}, got {actual_mode.value}")
        
        return is_consistent
    
    def _cleanup_temp_files(self) -> None:
        """Cleanup temporary transcription files."""
        import glob
        
        try:
            # Clean up any leftover temporary audio files
            temp_pattern = "/tmp/tmp*.wav"  # Unix-like systems
            if os.name == 'nt':  # Windows
                temp_pattern = os.path.join(tempfile.gettempdir(), "tmp*.wav")
            
            temp_files = glob.glob(temp_pattern)
            cleaned_count = 0
            
            for temp_file in temp_files:
                try:
                    # Only clean files older than 1 hour
                    file_age = time.time() - os.path.getmtime(temp_file)
                    if file_age > 3600:  # 1 hour
                        os.unlink(temp_file)
                        cleaned_count += 1
                except OSError:
                    pass  # File may already be deleted
            
            if cleaned_count > 0:
                logger.debug(f"Cleaned up {cleaned_count} temporary audio files")
                
        except Exception as e:
            logger.warning(f"Error during temp file cleanup: {e}")
    
    def _get_queue_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about internal queues and processing state.
        
        Returns:
            Dictionary with queue metrics
        """
        with self._lock:
            return {
                "transcript_entries_you": len(self.transcript_data["You"]),
                "transcript_entries_speaker": len(self.transcript_data["Speaker"]),
                "is_running": self._is_running,
                "processing_thread_alive": (
                    self._processing_thread.is_alive() 
                    if self._processing_thread else False
                ),
                "audio_sources_count": len(self.audio_sources)
            }


# Legacy compatibility function
def transcribe_audio_queue(transcriber: AudioTranscriber, speaker_queue: queue.Queue, mic_queue: queue.Queue) -> None:
    """
    Legacy compatibility function for the old transcribe_audio_queue method.
    
    Args:
        transcriber: AudioTranscriber instance
        speaker_queue: Speaker audio queue
        mic_queue: Microphone audio queue
    """
    transcriber.start_transcription(speaker_queue, mic_queue)