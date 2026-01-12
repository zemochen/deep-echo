import threading
from AudioTranscriber import AudioTranscriber
from src.ai.responder import GPTResponder
from src.ai.adapter import AIAdapter
import customtkinter as ctk
import AudioRecorder
import queue
import time
import sys
import TranscriberModels
import subprocess
import UILayout as layout
from src.ui.main_window import MainWindow
from keys import OPENAI_API_KEY, VOLCENGINE_API_KEY


def main():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

    speaker_queue = queue.Queue()
    mic_queue = queue.Queue()

    user_audio_recorder = AudioRecorder.DefaultMicRecorder()
    user_audio_recorder.record_into_queue(mic_queue)

    time.sleep(2)

    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(speaker_queue)

    model = TranscriberModels.get_model('--api' in sys.argv)

    transcriber = AudioTranscriber(user_audio_recorder.source, speaker_audio_recorder.source, model)
    transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(speaker_queue, mic_queue))
    transcribe.daemon = True
    transcribe.start()

    # Initialize AI adapter with default provider
    ai_adapter = AIAdapter()
    
    # Try to set up a provider with available API keys
    try:
        if OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'):
            # Use OpenAI as default provider
            openai_provider = ai_adapter.create_provider("openai", OPENAI_API_KEY)
            ai_adapter.set_provider(openai_provider)
            print(f"Using OpenAI provider with model: {openai_provider.get_model_name()}")
        elif VOLCENGINE_API_KEY:
            # Use Volcano Engine as fallback
            volcano_provider = ai_adapter.create_provider("volcano", VOLCENGINE_API_KEY)
            ai_adapter.set_provider(volcano_provider)
            print(f"Using Volcano Engine provider with model: {volcano_provider.get_model_name()}")
        else:
            print("WARNING: No valid API keys found. AI responses will not work.")
            # Create a dummy provider for testing
            from src.ai.providers.base_provider import AIProvider
            class DummyProvider(AIProvider):
                def __init__(self):
                    super().__init__("dummy-key", "dummy-model")
                def generate_response(self, prompt: str, **kwargs) -> str:
                    return "No AI provider configured"
                def get_provider_name(self) -> str:
                    return "dummy"
            ai_adapter.set_provider(DummyProvider())
    except Exception as e:
        print(f"Error setting up AI provider: {e}")
        # Create a dummy provider as fallback
        from src.ai.providers.base_provider import AIProvider
        class DummyProvider(AIProvider):
            def __init__(self):
                super().__init__("dummy-key", "dummy-model")
            def generate_response(self, prompt: str, **kwargs) -> str:
                return f"AI provider error: {e}"
            def get_provider_name(self) -> str:
                return "dummy"
        ai_adapter.set_provider(DummyProvider())

    responder = GPTResponder(ai_adapter)
    respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
    respond.daemon = True
    respond.start()

    # Check if we should use the new UI
    use_new_ui = '--new-ui' in sys.argv
    
    if use_new_ui:
        # Use new main window with AI provider selection
        main_window = MainWindow()
        root = main_window.initialize(transcriber, responder, ai_adapter, speaker_queue, mic_queue)
        
        print("READY - Using new UI with AI provider selection")
        main_window.run()
    else:
        # Use legacy UI for backward compatibility
        root = layout.init_ui()

        transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label, freeze_button = layout.create_ui_components(
            root, transcriber, speaker_queue, mic_queue)

        freeze_state = [False]  # Using list to be able to change its content inside inner functions

        def freeze_unfreeze():
            freeze_state[0] = not freeze_state[0]  # Invert the freeze state
            freeze_button.configure(text="Unfreeze" if freeze_state[0] else "Freeze")
            return freeze_state[0]

        freeze_button.configure(command=freeze_unfreeze)

        update_interval_slider_label.configure(text=f"Update interval: {update_interval_slider.get()} seconds")

        print("READY - Using legacy UI")
        layout.update_transcript_UI(transcriber, transcript_textbox)
        layout.update_response_UI(responder, response_textbox, update_interval_slider_label, update_interval_slider, freeze_state)

        root.mainloop()


if __name__ == "__main__":
    main()
