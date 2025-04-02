
# 🎧 DeepEcho

DeepEcho is a live transcription tool that uses OpenAI's GPT-3 model to provide real-time transcription and response suggestions. It is designed to assist users in transcribing conversations, meetings, lectures, and other spoken content. DeepEcho can be used to generate accurate transcriptions of spoken content, which can be helpful for note-taking, accessibility, and content creation purposes.

## 📖 Demo

TBC

## 🚀 Getting Started

Follow these steps to set up and run DeepEcho on your local machine.

### 📋 Prerequisites

- Python >=3.8.0
- An OpenAI API key that can access OpenAI API (set up a paid account OpenAI account)
- Windows OS / MacOS
- FFmpeg 

If FFmpeg is not installed in your system, you can follow the steps below to install it.

#### Windows

First, you need to install Chocolatey, a package manager for Windows. Open your PowerShell as Administrator and run the following command:
```
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```
Once Chocolatey is installed, you can install FFmpeg by running the following command in your PowerShell:
```
choco install ffmpeg
```
Please ensure that you run these commands in a PowerShell window with administrator privileges. If you face any issues during the installation, you can visit the official Chocolatey and FFmpeg websites for troubleshooting.
#### MacOS

1. Install Homebrew
```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
2. Install dependency

```shell
brew install ffmpeg
brew install portaudio
brew install python-tk
```
3. Install BlackHole

```shell
brew install blackhole-2ch
```
**Configuration BlackHole:**

* Open `Audio MIDI Setup`（ macOS in"Application > Others"）。
* Setup Multi-Output Device
* In Audio MIDI Setup → Audio Devices right-click on the newly created Multi-Output and select "Use This Device For Sound Output"
* Open digital audio workstation (DAW) such as GarageBand and set input device to "BlackHole"
* Set track to input from channel 1-2
*Play audio from another application and monitor or record in your DAW

> For more BlackHole see:[BlackHole github](https://github.com/ExistentialAudio/BlackHole)


### 🔧 Installation

1. Clone the repository:

   ```
   git clone https://github.com/zemochen/deep_echo.git
   ```

2. Navigate to the `deep_echo` folder:

   ```
   cd deep_echo
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```
   
4. Create a `keys.py` file in the DeepEcho directory and add your OpenAI API key:

   - Option 1: You can utilize a command on your command prompt. Run the following command, ensuring to replace "API KEY" with your actual OpenAI API key:

      ```
      python -c "with open('keys.py', 'w', encoding='utf-8') as f: f.write('OPENAI_API_KEY=\"API KEY\"')"
      ```

   - Option 2: You can create the keys.py file manually. Open up your text editor of choice and enter the following content:
   
      ```
      OPENAI_API_KEY="API KEY"
      ```
      Replace "API KEY" with your actual OpenAI API key. Save this file as keys.py within the DeepEcho directory.

### 🎬 Running DeepEcho

Run the main script:

```
python main.py
```

For a more better and faster version that also works with most languages, use:

```
python main.py --api
```

Upon initiation, DeepEcho will begin transcribing your microphone input and speaker output in real-time, generating a suggested response based on the conversation. Please note that it might take a few seconds for the system to warm up before the transcription becomes real-time.

The --api flag will use the whisper api for transcriptions. This significantly enhances transcription speed and accuracy, and it works in most languages (rather than just English without the flag). It's expected to become the default option in future releases. However, keep in mind that using the Whisper API will consume more OpenAI credits than using the local model. This increased cost is attributed to the advanced features and capabilities that the Whisper API provides. Despite the additional expense, the substantial improvements in speed and transcription accuracy may make it a worthwhile investment for your use case.

### ⚠️ Limitations

While DeepEcho provides real-time transcription and response suggestions, there are several known limitations to its functionality that you should be aware of:

**Default Mic and Speaker:** DeepEcho is currently configured to listen only to the default microphone and speaker set in your system. It will not detect sound from other devices or systems. If you wish to use a different mic or speaker, you will need to set it as your default device in your system settings.

**Whisper Model**: If the --api flag is not used, we utilize the 'tiny' version of the Whisper ASR model, due to its low resource consumption and fast response times. However, this model may not be as accurate as the larger models in transcribing certain types of speech, including accents or uncommon words.

**Language**: If you are not using the --api flag the Whisper model used in DeepEcho is set to English. As a result, it may not accurately transcribe non-English languages or dialects. We are actively working to add multi-language support to future versions of the program.

## 📖 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve DeepEcho.

### Code Style
For code style, we follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines. We recommend using a linter like [flake8](https://flake8.pycqa.org/en/latest/) to ensure your code adheres to these guidelines.