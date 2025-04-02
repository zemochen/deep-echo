from .AudioFactory import get_audio_device

# 暴露给外部使用的函数
def get_default_speaker():
    audio_interface = get_audio_device()
    return audio_interface.get_default_speaker()
