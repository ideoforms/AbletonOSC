import time
import pytest

#--------------------------------------------------------------------------------
# Add . to the path so that pythonosc can be imported, enabling unit testing
# without any external dependencies
#--------------------------------------------------------------------------------
import sys
sys.path.append(".")

from pathlib import Path
import wave
import struct

from ..client import AbletonOSCClient, TICK_DURATION

# Live tick is 100ms. Wait for this long plus a short additional buffer.
TICK_DURATION = 0.125

@pytest.fixture(scope="module")
def client() -> AbletonOSCClient:
    client = AbletonOSCClient()
    yield client
    client.stop()

@pytest.fixture(scope="function")
def silent_audio_file() -> Path:
    """
    Create a silent WAV file in the tests directory for audio-clip tests.
    """
    path = Path(__file__).resolve().parent / "silent_8s.wav"
    if not path.exists():
        duration_s = 8.0
        sample_rate = 48000
        channels = 1
        sample_width = 2  # 16-bit
        total_frames = int(duration_s * sample_rate)
        chunk_frames = 4096
        silence_chunk = struct.pack("<h", 0) * chunk_frames
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            frames_remaining = total_frames
            while frames_remaining > 0:
                frames = min(chunk_frames, frames_remaining)
                wf.writeframes(silence_chunk[: frames * sample_width])
                frames_remaining -= frames
    yield path
    remove_audio_file(path)

def wait_one_tick():
    """
    Sleep for one Ableton Live tick (100ms).
    """
    time.sleep(TICK_DURATION)

def remove_audio_file(path: Path) -> None:
    for target in (path, Path(str(path) + ".asd")):
        try:
            target.unlink()
        except FileNotFoundError:
            pass

c = AbletonOSCClient()
c.send_message("/live/api/reload")
c.stop()
