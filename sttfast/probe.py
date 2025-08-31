import subprocess, json, shutil
from pathlib import Path

def get_duration_sec(path: Path) -> float | None:
    """Return media duration in seconds using ffprobe; None if unknown."""
    if shutil.which("ffprobe") is None:
        return None
    try:
        # compact JSON so parsing is stable
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "format=duration",
            "-of", "json", str(path)
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        data = json.loads(out)
        dur = data.get("format", {}).get("duration")
        return float(dur) if dur is not None else None
    except Exception:
        return None
