# sttfast-core (CLI)

Lightweight, GPU-accelerated **speech‑to‑text backend** with a clean, modular CLI.  
Runs locally for privacy. Built around **faster‑whisper** with pragmatic presets and CPU‑side sentiment/tones.

---

## Install (dev)

```bash
# from the repo root
pip install -e .

# optional: test tools
pip install pytest pytest-timeout
```

> Python 3.10+ recommended. GPU acceleration requires a CUDA-capable GPU and the correct PyTorch/CT2 build. Falls back to CPU.

---

## Quick start

```bash
# See all commands
sttfast --help

# Transcribe a folder (moves media by default)
sttfast transcribe "C:\path\to\media"

# Copy instead of move
sttfast transcribe "C:\path\to\media" --copy

# Custom parent folder name (otherwise a timestamp is used)
sttfast transcribe "C:\path\to\media" --parent-name Interview_Run_A

# Temporary mode (no permanent output; cache-only)
sttfast temporary "C:\path\to\file.mp3"

# Search across all transcripts
sttfast search "exact phrase or keyword"

# Open media at timestamp (seconds.fraction)
sttfast openat "C:\sttfast_out\RunX\material\file.mp3" 207.52

# Export merged TXT (no timestamps)
sttfast export "C:\sttfast_out\RunX" --format txt

# Dry-run: list files, durations, and which preset would be used
sttfast dry-run "C:\path\to\media"
```

---

## Commands & Options

### `transcribe` — batch or single file

Transcribes file(s)/folder(s), creates the standard output layout, **moves media by default**.

```
sttfast transcribe [OPTIONS] INPUTS...
```

**Positional**  
- `INPUTS...` — one or more files and/or folders.

**Key options**
- `--copy` — copy the source into the run’s `material/` instead of moving it.
- `--parent-name TEXT` — custom parent folder name (default: timestamp).
- `--mode [auto|short|standard|long]` — decoding preset.
  - `auto` (default): decide per file by duration (short ≤30s; long ≥30min; else standard)
  - `short`: optimized for 0–30s clips (greedy decoding, fast VAD)
  - `standard`: balanced settings (greedy decoding, context on)
  - `long`: for multi‑minute/hour files (beam search, more context)
- `--language TEXT` — language hint (e.g., `en`, `fr`). Skips autodetect; helpful for noisy/short audio.
- `--long-beam INTEGER` — beam size used **only** when `mode` is `long` (default: 3; 1–8).
- `--long-best-of INTEGER` — best‑of candidates used **only** when `mode` is `long` (default: 3; 1–8).
- `--whisperx` — *(placeholder; no-op today)* reserved to enable future WhisperX integration (word‑level timestamps, diarization).

**Examples**
```bash
# Mixed folder (auto per file)
sttfast transcribe "D:\mixed_media"

# Force long preset with wider beam for accuracy
sttfast transcribe "D:\lectures" --mode long --long-beam 5 --long-best-of 5

# Hint language to improve stability on short/noisy clips
sttfast transcribe "D:\clips" --mode short --language en

# Copy originals instead of moving; custom parent name
sttfast transcribe "D:\clips" --copy --parent-name Interview_Run_A
```

---

### `temporary` — one-off run, no persistence

Processes a single file; results live in an in‑app cache and are overwritten by the next temporary run.

```
sttfast temporary [OPTIONS] FILE
```

**Options** (same spirit as `transcribe` but scoped to a single file):
- `--mode [auto|short|standard|long]`
- `--language TEXT`
- `--long-beam INTEGER`
- `--long-best-of INTEGER`

**Example**
```bash
sttfast temporary "C:\file.mp3" --mode auto
```

---

### `search` — full‑text across transcripts

Searches your master transcripts store.

```
sttfast search QUERY
```

**Example**
```bash
sttfast search "machine learning"
```

> Output shows file/run and matching snippets with timestamps.

---

### `openat` — clickable timestamp launcher

Launches your configured media player at a specific time.

```
sttfast openat MEDIA_FILE SECONDS
```

**Example**
```bash
sttfast openat "C:\sttfast_out\Interview_Run_A\material\file.mp3" 207.52
```

> On Windows and Linux the player is auto-detected in this order:
VLC → mpv → ffplay.
- "If VLC is found on PATH, it is used with `--start-time`."
- "Otherwise, if mpv (**NOT** tested) is found, it is used with `--start`."
- "Otherwise, ffplay (bundled with FFmpeg) is used as a fallback."

You can override detection with `--player vlc` or `--player mpv`.

---

### `export` — merge/format transcripts

Exports one run (or selected files) into a single file.

```
sttfast export [OPTIONS] RUN_OR_FOLDER
```

**Common options**
- `--format [txt|jsonl|srt]` — output format (default: `txt`).
- `--no-timestamps` — omit timestamps in TXT/JSONL.
- `--no-tones` — omit sentiment/tone annotations.

**Examples**
```bash
# Single merged TXT without timestamps
sttfast export "C:\sttfast_out\Interview_Run_A" --format txt --no-timestamps

# JSONL with everything included
sttfast export "C:\sttfast_out\Interview_Run_A" --format jsonl
```

---

### `dry-run` — plan before you run

Lists media files, their durations, and which preset would be chosen — **no transcription**.

```
sttfast dry-run [OPTIONS] INPUTS...
```

**Options**
- `--mode [auto|short|standard|long]` — manual override (applies to all listed files).

**Examples**
```bash
# Let the tool classify short/standard/long per file
sttfast dry-run "D:\mixed_media"

# Force "short" (useful for quick timing estimates)
sttfast dry-run "D:\mixed_media" --mode short
```

---

## Output layout

By default, each run creates a parent folder inside `sttfast_out/`, either timestamped or your `--parent-name`, with these subfolders:

```
sttfast_out/
└─ 2025-08-31_14-33-00/        # or your --parent-name
   ├─ material/                # moved/copied source media
   └─ transcripts/             # JSON/JSONL/SRT/TXT outputs
```

Clicking timestamps in your transcript viewer should call `sttfast openat` with the appropriate file & time.

---

## Tests

```bash
pytest
```

- `tests/test_probe.py` — duration probe smoke test  
- `tests/test_asr_smoke.py` — tiny‑model CPU smoke (skips if download unavailable)

---

## Notes

- `--whisperx` is present **as a placeholder** for future integration. It currently has no effect.
- `short/standard` presets use **greedy decoding** for speed; `long` uses **beam search** for accuracy (tunable via `--long-beam` / `--long-best-of`).

---

## Credits / Attribution
This project is licensed under the MIT License.  
If you use it in research, software, or derivative works, please credit **Aiman Al-Awdi (GitHub: [AAl-Awdi](https://github.com/AAl-Awdi))** as the original author of the `sttfast-core` project.  

