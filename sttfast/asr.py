from faster_whisper import WhisperModel
from pathlib import Path
from typing import Dict, Any, List, Literal, Optional
import json
from .probe import get_duration_sec

Preset = Literal["auto", "short", "standard", "long"]

# Tweak these thresholds if you like:
SHORT_MAX_S = 15          # ≤ 15s => "short"
LONG_MIN_S  = 30 * 60     # ≥ 30 min => "long"

# Public helper for CLI dry-run (no model load)
def choose_preset_for(path: Path, preset: Preset) -> tuple[str, float | None]:
    """
    Returns (preset_used, duration_seconds_or_None) without loading the ASR model.
    """
    if preset != "auto":
        forced = "short" if preset == "short" else ("long" if preset == "long" else "standard")
        dur = get_duration_sec(path)
        return forced, dur
    dur = get_duration_sec(path)
    if dur is None:
        return "standard", None
    if dur <= SHORT_MAX_S:
        return "short", dur
    if dur >= LONG_MIN_S:
        return "long", dur
    return "standard", dur


class ASR:
    def __init__(self, model_name: str, device: str, compute_type: str):
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def _choose_preset(self, path: Path, preset: Preset) -> Literal["short","standard","long"]:
        if preset != "auto":
            return "short" if preset == "short" else ("long" if preset == "long" else "standard")
        dur = get_duration_sec(path)
        if dur is None:
            # fallback: let model detect later; balanced params
            return "standard"
        if dur <= SHORT_MAX_S:
            return "short"
        if dur >= LONG_MIN_S:
            return "long"
        return "standard"

    def transcribe_path(
        self,
        path: Path,
        vad: bool = True,
        preset: Preset = "auto",
        language: Optional[str] = None,     # e.g. "en" to skip autodetect
        long_beam_size: int = 3,            # default beam for long files
        long_best_of: int = 3,              # default best_of for long files
    ) -> Dict[str, Any]:

        choice = self._choose_preset(path, preset)

        # Base kwargs common to all
        kw = dict(
            vad_filter=vad,
            word_timestamps=False,
            temperature=0.0,
        )
        if language:
            kw["language"] = language

        if choice == "short":
            kw.update(
                dict(
                    vad_parameters=dict(min_silence_duration_ms=150),
                    beam_size=1,                        # GREEDY
                    best_of=1,
                    condition_on_previous_text=False,
                    no_speech_threshold=0.6,
                    log_prob_threshold=-1.0,
                )
            )
        elif choice == "long":
            kw.update(
                dict(
                    vad_parameters=dict(min_silence_duration_ms=400),
                    beam_size=long_beam_size,           # BEAM (tunable)
                    best_of=long_best_of,               # BEAM (tunable)
                    condition_on_previous_text=True,
                    #patience=1.0,   # patience omitted -> use library default (must be > 0 when beam_size > 1)
                )
            )
        else:  # "standard"
            kw.update(
                dict(
                    vad_parameters=dict(min_silence_duration_ms=250),
                    beam_size=1,                        # GREEDY by default for speed
                    best_of=1,
                    condition_on_previous_text=True,
                )
            )

        segments, info = self.model.transcribe(str(path), **kw)
        out = []
        for s in segments:
            out.append({"start": s.start, "end": s.end, "text": s.text.strip()})
        return {"language": info.language, "duration": info.duration, "segments": out, "preset_used": choice}

def to_srt(segments: List[dict]) -> str:
    def fmt(t):
        h = int(t//3600); m = int((t%3600)//60); s = int(t%60); ms = int((t - int(t))*1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    lines=[]
    for i,s in enumerate(segments, start=1):
        lines += [str(i), f"{fmt(s['start'])} --> {fmt(s['end'])}", s['text'], ""]
    return "\n".join(lines)

def to_jsonl(segments: List[dict]) -> str:
    return "\n".join(json.dumps(s, ensure_ascii=False) for s in segments)
