from enum import Enum
import typer, json
from pathlib import Path
from rich import print
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from .config import Settings
from .folders import make_parent, place_media, temp_cache_root, clear_temp_cache
from .asr import ASR, to_srt, choose_preset_for
from .db import open_db, insert_file, insert_segments
from .sentiment import label_text
from .media import open_at as launch_player
from .export import export_txt, export_json
from .search import search_phrase

class Mode(str, Enum):
    auto = "auto"
    short = "short"
    standard = "standard"
    long = "long"

app = typer.Typer(pretty_exceptions_show_locals=False)
S = Settings()

AUDIO_EXTS = {".wav",".mp3",".m4a",".flac",".aac",".ogg",".wma"}
VIDEO_EXTS = {".mp4",".mkv",".mov",".m4v",".avi",".webm"}
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS

def _gather(paths: list[Path]) -> list[Path]:
    out=[]
    for p in paths:
        if p.is_dir():
            out += [x for x in p.rglob("*") if x.suffix.lower() in MEDIA_EXTS]
        elif p.suffix.lower() in MEDIA_EXTS:
            out.append(p)
    return out

def _analyze_segments(segments):
    out=[]
    for s in segments:
        lab = label_text(s["text"])
        out.append({**s, **lab})
    return out

@app.command(help="Transcribe file(s)/folder(s). Move by default; use --copy to copy instead.")
def transcribe(
    inputs: list[Path] = typer.Argument(..., help="File(s) and/or folder(s)"),
    parent_name: str | None = typer.Option(None, help="Custom parent folder name; default is timestamp"),
    copy: bool = typer.Option(False, help="Copy instead of move source files"),
    whisperx: bool = typer.Option(False, help="(future) word-level timestamps with WhisperX"),
    mode: Mode = typer.Option(Mode.auto, help="Decoding preset per file: auto|short|standard|long"),
    language: Optional[str] = typer.Option(None, help="Language hint (e.g., en, fr). Skips autodetect."),
    long_beam: int = typer.Option(3, min=1, max=8, help="Beam size for LONG files (ignored for short/standard)"),
    long_best_of: int = typer.Option(3, min=1, max=8, help="Best-of for LONG files (ignored for short/standard)"),
):


    parent = make_parent(S, parent_name)
    mat_dir, tr_dir = parent/"material", parent/"transcripts"
    asr = ASR(S.model_name, S.device, S.compute_type)
    con = open_db(S.db_path)

    files = _gather(inputs)
    if not files:
        print("[yellow]No media files found.[/yellow]")
        raise typer.Exit(code=1)

    with ThreadPoolExecutor(max_workers=S.max_workers) as pool:
        for f in files:
            placed = place_media(f, mat_dir, move=not copy)
            result = asr.transcribe_path(
                placed,
                vad=S.vad_enabled,
                preset=mode.value,
                language=language,
                long_beam_size=long_beam,
                long_best_of=long_best_of,
            )
            print(f"[dim]Preset used: {result.get('preset_used')}[/dim]")
            segs = result["segments"]

            # Sentiment/tone per segment on CPU in parallel
            segs = list(pool.map(lambda s: {**s, **label_text(s["text"])}, segs))

            # Save per-file outputs
            base = tr_dir / placed.stem
            (base.with_suffix(".srt")).write_text(to_srt(segs), encoding="utf-8")
            export_json(segs, base.with_suffix(".json"))
            export_txt(segs, base.with_suffix(".txt"), include_ts=True, include_tone=True)

            # Index into DB
            file_id = insert_file(con, placed, parent, result["duration"], result["language"])
            insert_segments(con, file_id, segs)

            print(f"[green]Done:[/green] {placed.name}  ({len(segs)} segments)")

@app.command(help="Temporary mode: process a single file; results live in a cache and are overwritten next run.")
def temporary(
    file: Path,
    mode: Mode = typer.Option(Mode.auto),
    language: Optional[str] = typer.Option(None),
    long_beam: int = typer.Option(3, min=1, max=8),
    long_best_of: int = typer.Option(3, min=1, max=8),
):
    if not file.exists() or file.suffix.lower() in {".json",".txt",".srt"}:
        print("[red]Provide a valid audio/video file.[/red]")
        raise typer.Exit(code=2)

    clear_temp_cache()
    cache = temp_cache_root()
    asr = ASR(S.model_name, S.device, S.compute_type)
    result = asr.transcribe_path(
        file,
        vad=S.vad_enabled,
        preset=mode.value,
        language=language,
        long_beam_size=long_beam,
        long_best_of=long_best_of,
    )

    segs = _analyze_segments(result["segments"])

    # Save transient outputs
    (cache / "temp.srt").write_text(to_srt(segs), encoding="utf-8")
    export_json(segs, cache / "temp.json")
    export_txt(segs, cache / "temp.txt", include_ts=True, include_tone=True)

    print(f"[bold]Temporary transcript ready:[/bold] {cache}  [dim](clears next run)[/dim]")

@app.command(help="Open a media file at a timestamp (seconds). Uses VLC/mpv, falls back to ffplay.")
def openat(media: Path, t: float):
    launch_player(S.media_player, media, t)

@app.command(help="Full-text search across all transcripts. Use quotes for phrases.")
def find(query: str):
    con = open_db(S.db_path)
    hits = list(search_phrase(con, query))
    if not hits:
        print("[yellow]No matches.[/yellow]")
        return
    for h in hits:
        print(f"[cyan]{h['file']}[/cyan]  [{h['start']:.2f}s]  {h['text'][:120]}")

@app.command(help="List each media file, its duration, and the preset that would be used (no transcription).")
def dry_run(
    inputs: list[Path] = typer.Argument(..., help="File(s) and/or folder(s)"),
    mode: Mode = typer.Option(Mode.auto, help="auto|short|standard|long (manual override)"),
):
    files = _gather(inputs)
    if not files:
        print("[yellow]No media files found.[/yellow]")
        raise typer.Exit(code=1)

    def fmt_dur(d):
        if d is None:
            return "unknown"
        s = int(d)
        h, r = divmod(s, 3600)
        m, s = divmod(r, 60)
        return f"{h:02}:{m:02}:{s:02}"

    print("[bold]Dry run (no transcription):[/bold]")
    for f in files:
        preset_used, dur = choose_preset_for(f, mode.value)
        print(f"• {f}  |  duration={fmt_dur(dur)}  |  preset={preset_used}")


@app.command(help="Export JSON transcripts to a TXT file (merged or separate) with toggle flags.")
def export(
    paths: list[Path],
    out: Path,
    merged: bool = typer.Option(False, help="Merge into one file"),
    no_ts: bool = typer.Option(False, help="Exclude timestamps"),
    no_tone: bool = typer.Option(False, help="Exclude sentiment/tones"),
):
    import json
    include_ts = not no_ts
    include_tone = not no_tone
    seglists=[]
    for p in paths:
        if p.suffix.lower() != ".json":
            print(f"[yellow]Skipping non-JSON: {p}[/yellow]")
            continue
        seglists.append(json.loads(p.read_text(encoding="utf-8")))
    if not seglists:
        print("[yellow]No valid JSON transcripts provided.[/yellow]")
        return

    from itertools import chain
    out.parent.mkdir(parents=True, exist_ok=True)
    if merged:
        export_txt(list(chain.from_iterable(seglists)), out, include_ts, include_tone)
        print(f"[green]Exported merged ->[/green] {out}")
    else:
        for i, segs in enumerate(seglists, start=1):
            fp = out.with_name(out.stem + f"_{i}" + out.suffix)
            export_txt(segs, fp, include_ts, include_tone)
            print(f"[green]Exported ->[/green] {fp}")

if __name__ == "__main__":
    app()
