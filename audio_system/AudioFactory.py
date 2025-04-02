import platform
from .WindowsAudio import WindowsAudio
from .MacOSAudio import MacOSAudio

def get_audio_device():
    """根据系统返回具体的音频接口实现"""
    system = platform.system()
    if system == "Windows":
        return WindowsAudio()
    elif system == "Darwin":  # macOS
        return MacOSAudio()
    else:
        raise NotImplementedError(f"Unsupported system: {system}")
