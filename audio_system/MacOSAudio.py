from .AudioInterface import AudioInterface
import pyaudio


class MacOSAudio(AudioInterface):
    def find_blackhole_device(self, p):
        # find blackhole
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if "BlackHole" in dev["name"] and dev["maxInputChannels"] > 0:
                print(
                    f"Found BlackHole device: {dev['name']} (Index: {dev['index']})")
                return dev
        raise Exception(
            "BlackHole device not found. Please ensure it is installed and configured.")

    def get_default_speaker(self):
        p = pyaudio.PyAudio()
        try:
            # find blackhole
            blackhole_device = self.find_blackhole_device(p)
        finally:
            p.terminate()
        return blackhole_device

