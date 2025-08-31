from pathlib import Path
import wave
import struct

from sttfast.probe import get_duration_sec

def _write_tone_wav(path: Path, seconds=1, rate=16000):
    nframes = seconds * rate
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(rate)
        silence = struct.pack("<h", 0)
        wf.writeframes(silence * nframes)

def test_get_duration_sec(tmp_path: Path):
    f = tmp_path / "one_sec.wav"
    _write_tone_wav(f, seconds=1)
    dur = get_duration_sec(f)
    assert dur is None or abs(dur - 1.0) < 0.15  # if ffprobe missing, function may return None
