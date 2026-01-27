"""
GPT Responder module for generating AI responses based on conversation transcripts.

This module provides the GPTResponder class that uses the AI adapter architecture
to generate intelligent response suggestions from conversation transcripts.
"""

import time
import logging
from datetime import datetime
from typing import Optional, Callable
import threading

from .adapter import AIAdapter
from .providers.base_provider import AIProviderError
from backend.utils.threading import get_thread_manager, ThreadPriority, ManagedThread
from backend.utils.resource_optimizer import get_resource_optimizer

logger = logging.getLogger(__name__)

# Default prompt template for generating responses
DEFAULT_PROMPT_TEMPLATE = """You are a casual pal, genuinely interested in the conversation at hand. A poor transcription of conversation is given below. 
        
{transcript}.

Please respond, in detail, to the conversation. Confidently give a straightforward response to the speaker, \
even if you don't understand them. Give your response in square brackets.\
 DO NOT ask to repeat, \
  DO NOT ask for clarification. Just answer the speaker directly.\
 Respond in the same language as the speaker."""

INITIAL_RESPONSE = "Welcome to Ecoute 👋"


def create_prompt(transcript: str, template: str = DEFAULT_PROMPT_TEMPLATE) -> str:
    """
    Create a prompt for AI response generation from transcript.
    
    Args:
        transcript: The conversation transcript
        template: Optional custom prompt template
        
    Returns:
        Formatted prompt string
    """
    return template.format(transcript=transcript)


def generate_response_from_transcript(transcript: str, ai_adapter: AIAdapter, 
                                    prompt_template: str = DEFAULT_PROMPT_TEMPLATE) -> str:
    """
    Generate AI response from transcript using the AI adapter.
    
    Args:
        transcript: The conversation transcript
        ai_adapter: AI adapter instance for generating responses
        prompt_template: Optional custom prompt template
        
    Returns:
        Generated response text, empty string if generation fails
    """
    try:
        prompt = create_prompt(transcript, prompt_template)
        response = ai_adapter.generate_response(prompt)
        
        # Extract response from square brackets if present
        try:
            if '[' in response and ']' in response:
                return response.split('[')[1].split(']')[0]
            else:
                return response
        except (IndexError, AttributeError):
            return response
            
    except Exception as e:
        logger.error(f"Failed to generate response from transcript: {e}")
        return ''


class GPTResponder:
    """
    GPT Responder for generating AI response suggestions based on conversation transcripts.
    
    This class manages the response generation process using the AI adapter architecture,
    supports configurable update intervals, and provides proper error handling with retry logic.
    """
    
    def __init__(self, ai_adapter: AIAdapter, response_interval: int = 2, 
                 max_retries: int = 3, retry_delay: float = 1.0,
                 prompt_template: str = DEFAULT_PROMPT_TEMPLATE):
        """
        Initialize the GPT responder.
        
        Args:
            ai_adapter: AI adapter instance for generating responses
            response_interval: Interval between response updates in seconds
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Base delay between retries in seconds (exponential backoff)
            prompt_template: Custom prompt template for response generation
        """
        if not ai_adapter:
            raise ValueError("AI adapter is required")
        
        self.ai_adapter = ai_adapter
        self.response = INITIAL_RESPONSE
        self.response_interval = response_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.prompt_template = prompt_template
        
        # Thread control with managed threading
        self._stop_event = threading.Event()
        self._response_thread: Optional[ManagedThread] = None
        self._thread_manager = get_thread_manager()
        self._resource_optimizer = get_resource_optimizer()
        
        # Register memory optimization callback
        self._resource_optimizer.memory_optimizer.register_optimization_callback(
            self._optimize_memory_usage
        )
        
        logger.info(f"GPT Responder initialized with {ai_adapter.get_current_provider()} provider")
    
    def respond_to_transcriber(self, transcriber) -> None:
        """
        Start responding to transcriber updates in a separate thread.
        
        Args:
            transcriber: Audio transcriber instance to monitor for updates
        """
        if self._response_thread and self._response_thread.is_alive():
            logger.warning("Response thread is already running")
            return
        
        self._stop_event.clear()
        
        # Create managed thread for response generation
        self._response_thread = self._thread_manager.create_thread(
            name=f"GPTResponder_{id(self)}",
            target=self._response_loop,
            args=(transcriber,),
            daemon=True,
            priority=ThreadPriority.NORMAL,  # Normal priority for AI responses
            auto_start=True
        )
        
        if self._response_thread:
            logger.info("Started GPT responder with managed thread")
        else:
            logger.error("Failed to create GPT responder thread")
    
    def stop_responding(self) -> None:
        """Stop the response generation thread."""
        if self._response_thread:
            self._stop_event.set()
            success = self._response_thread.stop(timeout=3.0)
            if success:
                # Remove thread from manager
                self._thread_manager.remove_thread(self._response_thread.name)
                logger.info("Stopped GPT responder thread")
            else:
                logger.warning("GPT responder thread did not stop gracefully")
    
    def _response_loop(self, transcriber) -> None:
        """
        Main response generation loop.
        
        Args:
            transcriber: Audio transcriber instance to monitor
        """
        # Validate transcriber is properly initialized
        if not transcriber:
            logger.error("Transcriber is None - cannot start response loop")
            return
        
        if not hasattr(transcriber, 'transcript_changed_event'):
            logger.error("Transcriber missing transcript_changed_event - cannot start response loop")
            return
        
        if not hasattr(transcriber, 'get_transcript'):
            logger.error("Transcriber missing get_transcript method - cannot start response loop")
            return
        
        logger.info("Response loop started successfully with valid transcriber")
        last_submit = datetime.utcnow()
        
        while not self._stop_event.is_set():
            try:
                # Check if thread should stop (with safety check)
                if self._response_thread and self._response_thread.should_stop():
                    break
                
                if transcriber.transcript_changed_event.is_set():
                    start_time = time.time()
                    
                    # Clear the event and get transcript
                    transcriber.transcript_changed_event.clear()
                    transcript_string = transcriber.get_transcript()
                    last_submit, speaker_string = transcriber.get_speaker_newest(last_submit)
                    
                    # Generate response if there's new speaker content
                    response = ''
                    if speaker_string:
                        response = self._generate_response_with_retry(transcript_string)
                        # Update thread metrics (with safety check)
                        if self._response_thread:
                            self._response_thread.increment_processed_items()
                    
                    # Update response if generation was successful
                    if response:
                        self.response = response
                        logger.debug(f"Updated response: {response[:50]}...")
                    
                    # Maintain response interval timing
                    end_time = time.time()
                    execution_time = end_time - start_time
                    remaining_time = self.response_interval - execution_time
                    
                    if remaining_time > 0:
                        self._stop_event.wait(remaining_time)
                else:
                    # Wait briefly before checking again
                    self._stop_event.wait(0.3)
                    
            except Exception as e:
                logger.error(f"Error in response loop: {e}")
                # Update error count (with safety check)
                if self._response_thread:
                    self._response_thread.increment_error_count()
                self._stop_event.wait(1.0)  # Wait before retrying
    
    def _generate_response_with_retry(self, transcript: str) -> str:
        """
        Generate response with retry logic and exponential backoff.
        
        Args:
            transcript: The conversation transcript
            
        Returns:
            Generated response text, empty string if all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                return generate_response_from_transcript(
                    transcript, 
                    self.ai_adapter, 
                    self.prompt_template
                )
            except AIProviderError as e:
                logger.warning(f"AI provider error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for response generation")
            except Exception as e:
                logger.error(f"Unexpected error during response generation: {e}")
                break
        
        return ''
    
    def update_response_interval(self, interval: int) -> None:
        """
        Update the response generation interval.
        
        Args:
            interval: New interval in seconds
            
        Raises:
            ValueError: If interval is not positive
        """
        if interval <= 0:
            raise ValueError("Response interval must be positive")
        
        old_interval = self.response_interval
        self.response_interval = interval
        logger.info(f"Response interval updated from {old_interval}s to {interval}s")
    
    def switch_ai_provider(self, provider) -> None:
        """
        Switch to a new AI provider.
        
        Args:
            provider: New AI provider instance
        """
        old_provider = self.ai_adapter.get_current_provider()
        self.ai_adapter.set_provider(provider)
        new_provider = self.ai_adapter.get_current_provider()
        logger.info(f"AI provider switched from {old_provider} to {new_provider}")
    
    def get_current_response(self) -> str:
        """
        Get the current response.
        
        Returns:
            Current response text
        """
        return self.response
    
    def get_response_interval(self) -> int:
        """
        Get the current response interval.
        
        Returns:
            Current response interval in seconds
        """
        return self.response_interval
    
    def get_ai_provider_info(self) -> dict:
        """
        Get information about the current AI provider.
        
        Returns:
            Dictionary containing provider information
        """
        return {
            "provider": self.ai_adapter.get_current_provider(),
            "model": self.ai_adapter.get_current_model(),
            "config": self.ai_adapter.get_provider_config()
        }
    
    def is_responding(self) -> bool:
        """
        Check if the responder is currently active.
        
        Returns:
            True if response thread is running, False otherwise
        """
        return self._response_thread is not None and self._response_thread.is_alive()
    
    def get_status(self) -> dict:
        """
        Get the current status of the GPT responder.
        
        Returns:
            Dictionary containing responder status information
        """
        return {
            "is_responding": self.is_responding(),
            "response_interval": self.response_interval,
            "current_response": self.response,
            "ai_provider": self.get_ai_provider_info(),
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }
    
    def _optimize_memory_usage(self) -> float:
        """
        Optimize memory usage by clearing old response data.
        
        Returns:
            Estimated memory freed in MB
        """
        # Clear response if it's very long (keep only last 1000 characters)
        initial_length = len(self.response)
        if initial_length > 1000:
            self.response = self.response[-1000:]
            chars_removed = initial_length - len(self.response)
            
            # Rough estimate: 1 byte per character
            estimated_freed = chars_removed / (1024 * 1024)  # MB
            
            logger.debug(f"GPT Responder memory optimization freed ~{estimated_freed:.4f}MB")
            return estimated_freed
        
        return 0.0