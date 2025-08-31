from pathlib import Path
from .config import Settings, timestamp_name
import shutil

def make_parent(settings: Settings, custom: str | None) -> Path:
    name = custom or timestamp_name()
    parent = settings.parent_dir / name
    (parent / "material").mkdir(parents=True, exist_ok=True)
    (parent / "transcripts").mkdir(exist_ok=True)
    return parent

def place_media(src: Path, dest_dir: Path, move: bool) -> Path:
    dest = dest_dir / src.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(src), str(dest))
        return dest
    else:
        shutil.copy2(src, dest)
        return dest

def temp_cache_root() -> Path:
    p = Path.home() / ".sttfast_temp"
    p.mkdir(exist_ok=True)
    return p

def clear_temp_cache():
    root = temp_cache_root()
    for x in root.glob("*"):
        try:
            if x.is_file():
                x.unlink()
            else:
                shutil.rmtree(x, ignore_errors=True)
        except Exception:
            pass
