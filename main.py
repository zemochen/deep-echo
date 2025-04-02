import threading
from AudioTranscriber import AudioTranscriber
from GPTResponder import GPTResponder
import customtkinter as ctk
import AudioRecorder
import queue
import time
import sys
import TranscriberModels
import subprocess
import UILayout as layout


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

    responder = GPTResponder()
    respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
    respond.daemon = True
    respond.start()

    root = layout.init_ui()



    transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label,freeze_button = layout.create_ui_components(
        root, transcriber, speaker_queue, mic_queue)

    freeze_state = [False]  # Using list to be able to change its content inside inner functions

    def freeze_unfreeze():
        freeze_state[0] = not freeze_state[0]  # Invert the freeze state
        freeze_button.configure(text="Unfreeze" if freeze_state[0] else "Freeze")
        return freeze_state[0]

    freeze_button.configure(command=freeze_unfreeze)

    update_interval_slider_label.configure(text=f"Update interval: {update_interval_slider.get()} seconds")

    print("READY")
    layout.update_transcript_UI(transcriber, transcript_textbox)
    layout.update_response_UI(responder, response_textbox, update_interval_slider_label, update_interval_slider, freeze_state)

    root.mainloop()


if __name__ == "__main__":
    main()
