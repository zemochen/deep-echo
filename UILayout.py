import customtkinter as ctk

# freeze_state = [False]  # Using list to be able to change its content inside inner functions

def init_ui():
    root = ctk.CTk()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root.grid_rowconfigure(0, weight=100)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(0, weight=2)
    root.grid_columnconfigure(1, weight=1)


    root.title("Deep Echo")
    root.geometry("1000x600")

    # root.grid_columnconfigure(0, weight=1)
    # root.grid_rowconfigure(0, weight=1)
    return root


def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, textbox):
    transcript_string = transcriber.get_transcript()
    write_in_textbox(textbox, transcript_string)
    textbox.after(300, update_transcript_UI, transcriber, textbox)

def update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider,freeze_state):
    if not freeze_state[0]:
        response = responder.response

        textbox.configure(state="normal")
        write_in_textbox(textbox, response)
        textbox.configure(state="disabled")

        update_interval = int(update_interval_slider.get())
        responder.update_response_interval(update_interval)
        update_interval_slider_label.configure(text=f"Update interval: {update_interval} seconds")

    textbox.after(300, update_response_UI, responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state)

def clear_context(transcriber, speaker_queue,mic_queue):
    transcriber.clear_transcript_data()

    with speaker_queue.mutex:
        speaker_queue.queue.clear()
    with mic_queue.mutex:
        mic_queue.queue.clear()

def create_ui_components(root, transcriber, speaker_queue, mic_queue):
    _font_size = 20
    # set theme


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

    response_textbox = ctk.CTkTextbox(root, width=300, font=("Arial", _font_size), text_color='#639cdc', wrap="word")
    response_textbox.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

    freeze_button = ctk.CTkButton(root, text="Freeze", command=None)
    freeze_button.grid(row=1, column=1, padx=10, pady=3, sticky="nsew")

    update_interval_slider = ctk.CTkSlider(root, from_=1, to=10, width=300, height=20, number_of_steps=9)
    update_interval_slider.set(2)
    update_interval_slider.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

    update_interval_slider_label = ctk.CTkLabel(root, text=f"", font=("Arial", 12), text_color="#FFFCF2")
    update_interval_slider_label.grid(row=2, column=1, padx=10, pady=3, sticky="nsew")
    # update_interval_slider_label.configure(text=f"Update interval: {update_interval_slider.get()} seconds")


    return transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label,freeze_button

