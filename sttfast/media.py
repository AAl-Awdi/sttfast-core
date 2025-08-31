import shutil, subprocess
from pathlib import Path

def _exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def open_at(player: str, file: Path, start_sec: float) -> None:
    """Open media at timestamp using VLC or mpv; fallback to ffplay (FFmpeg)."""
    start = max(0.0, float(start_sec))
    file = Path(file)
    cmd = None

    if player == "vlc" or (player == "auto" and _exists("vlc")):
        cmd = ["vlc", f"--start-time={start}", str(file)]
    elif player == "mpv" or (player == "auto" and _exists("mpv")):
        cmd = ["mpv", f"--start={start}", str(file)]
    else:
        # Fallback to ffplay (installed with FFmpeg in Step 1)
        # -autoexit closes when stream ends; -nodisp is audio-only if you want
        cmd = ["ffplay", "-ss", str(start), "-autoexit", str(file)]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
