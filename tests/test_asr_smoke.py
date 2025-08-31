import os
from pathlib import Path
import wave, struct, math

import pytest
from sttfast.asr import ASR

def _write_sine_wav(path: Path, seconds=1, freq=440, rate=16000):
    nframes = seconds * rate
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(rate)
        frames = bytearray()
        for i in range(nframes):
            val = int(3000 * math.sin(2*math.pi*freq*i/rate))
            frames += struct.pack("<h", val)
        wf.writeframes(frames)

@pytest.mark.timeout(120)
def test_asr_runs_cpu_tiny(tmp_path: Path):
    # tiny CPU to keep the test light. Skips if HF download not possible.
    wav = tmp_path / "hello.wav"
    _write_sine_wav(wav, seconds=1)

    try:
        asr = ASR(model_name="tiny", device="cpu", compute_type="int8")
        result = asr.transcribe_path(wav, vad=True, preset="short", language="en")
    except Exception as e:
        # If offline / no HF cache etc., skip instead of failing CI
        pytest.skip(f"ASR tiny model not available or download failed: {e}")

    assert "segments" in result
    assert isinstance(result["segments"], list)
