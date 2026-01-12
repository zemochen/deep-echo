"""
Legacy UI Layout module for backward compatibility.

This module provides backward compatibility with the existing UILayout interface
while delegating to the new refactored UI controller.
"""

import customtkinter as ctk
from src.ui.controller import UIController

# Global UI controller instance for backward compatibility
_ui_controller = None

def init_ui():
    """Initialize UI (backward compatibility wrapper)."""
    global _ui_controller
    _ui_controller = UIController()
    return _ui_controller.init_ui()


def write_in_textbox(textbox, text):
    """Write text in textbox (backward compatibility wrapper)."""
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, textbox):
    """Update transcript UI (backward compatibility wrapper)."""
    global _ui_controller
    if _ui_controller:
        _ui_controller.transcriber = transcriber
        _ui_controller.transcript_textbox = textbox
        _ui_controller.update_transcript_ui()
    else:
        # Fallback to original implementation
        transcript_string = transcriber.get_transcript()
        write_in_textbox(textbox, transcript_string)
        textbox.after(300, update_transcript_UI, transcriber, textbox)

def update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state):
    """Update response UI (backward compatibility wrapper)."""
    global _ui_controller
    if _ui_controller:
        _ui_controller.response_textbox = textbox
        _ui_controller.update_interval_label = update_interval_slider_label
        _ui_controller.update_interval_slider = update_interval_slider
        _ui_controller.freeze_state = freeze_state
        _ui_controller.update_response_ui(responder)
    else:
        # Fallback to original implementation
        if not freeze_state[0]:
            response = responder.get_current_response()

            textbox.configure(state="normal")
            write_in_textbox(textbox, response)
            textbox.configure(state="disabled")

            update_interval = int(update_interval_slider.get())
            responder.update_response_interval(update_interval)
            update_interval_slider_label.configure(text=f"Update interval: {update_interval} seconds")

        textbox.after(300, update_response_UI, responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state)

def clear_context(transcriber, speaker_queue, mic_queue):
    """Clear context (backward compatibility wrapper)."""
    transcriber.clear_transcript_data()

    with speaker_queue.mutex:
        speaker_queue.queue.clear()
    with mic_queue.mutex:
        mic_queue.queue.clear()

def create_ui_components(root, transcriber, speaker_queue, mic_queue):
    """Create UI components (backward compatibility wrapper)."""
    global _ui_controller
    if _ui_controller:
        _ui_controller.root = root
        components = _ui_controller.create_ui_components(transcriber, speaker_queue, mic_queue)
        
        # Set up clear context callback
        def clear_context_callback():
            clear_context(transcriber, speaker_queue, mic_queue)
        _ui_controller.set_clear_context_callback(clear_context_callback)
        
        return components
    else:
        # Fallback to original implementation
        return _create_ui_components_legacy(root, transcriber, speaker_queue, mic_queue)

def _create_ui_components_legacy(root, transcriber, speaker_queue, mic_queue):
    """Legacy UI components creation (fallback implementation)."""
    _font_size = 12

    main_frame = ctk.CTkFrame(root)
    main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=0)

    transcript_textbox = ctk.CTkTextbox(
        main_frame,
        font=("Arial", _font_size),
        text_color='#FFFCF2',
        wrap="word"
    )
    transcript_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    clear_button = ctk.CTkButton(
        main_frame,
        text="Clear Transcript",
        command=lambda: clear_context(transcriber, speaker_queue, mic_queue)
    )
    clear_button.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    right_frame = ctk.CTkFrame(root)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    right_frame.grid_columnconfigure(0, weight=1)
    right_frame.grid_rowconfigure(0, weight=100)
    right_frame.grid_rowconfigure(1, weight=1)
    right_frame.grid_rowconfigure(2, weight=1)
    right_frame.grid_rowconfigure(3, weight=1)

    response_textbox = ctk.CTkTextbox(right_frame, width=300, font=("Arial", _font_size), text_color='#639cdc', wrap="word")
    response_textbox.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

    freeze_button = ctk.CTkButton(right_frame, text="Freeze", command=None)
    freeze_button.grid(row=1, column=1, padx=10, pady=3, sticky="nsew")

    update_interval_slider = ctk.CTkSlider(right_frame, from_=1, to=10, width=300, height=20, number_of_steps=9)
    update_interval_slider.set(2)
    update_interval_slider.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

    update_interval_slider_label = ctk.CTkLabel(right_frame, text=f"", font=("Arial", 12), text_color="#FFFCF2")
    update_interval_slider_label.grid(row=2, column=1, padx=10, pady=3, sticky="nsew")

    return transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label, freeze_button

