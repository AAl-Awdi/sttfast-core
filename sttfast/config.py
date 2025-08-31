from pathlib import Path
from pydantic import BaseModel
from datetime import datetime

class Settings(BaseModel):
    model_name: str = "distil-large-v3" # or "large-v3"
    device: str = "cuda"                # "cpu" if no GPU
    compute_type: str = "int8_float16"  # "int8_float16" instead of "float16" for speed/memory
    use_whisperx: bool = False          # optional word-level timestamps later
    move_files: bool = True             # default move; toggle allows copy
    parent_dir: Path = Path.home() / "sttfast_out"
    db_path: Path = Path.home() / "sttfast_out" / "transcripts.sqlite"
    media_player: str = "auto"          # "auto" tries vlc→mpv→ffplay
    max_workers: int = 8                # CPU threads for VAD/sentiment/export
    vad_enabled: bool = True            # skip silence on long files
    diarization: bool = False           # optional later

def timestamp_name() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
