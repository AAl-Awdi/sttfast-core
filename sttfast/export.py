from pathlib import Path
import json

def export_txt(segments, fp: Path, include_ts=True, include_tone=True):
    fp.parent.mkdir(parents=True, exist_ok=True)
    with fp.open("w", encoding="utf-8") as f:
        for s in segments:
            ts = f"[{s['start']:.2f}-{s['end']:.2f}] " if include_ts else ""
            tone = ""
            if include_tone:
                tone = f"  ({s.get('sentiment')}"
                tones = s.get("tones", [])
                if tones: tone += f"; {', '.join(tones)}"
                tone += ")"
            f.write(f"{ts}{s['text']}{tone}\n")

def export_json(segments, fp: Path, include_tone=True):
    out = []
    for s in segments:
        row = {k: s[k] for k in ("start","end","text")}
        if include_tone:
            row["sentiment"] = s.get("sentiment")
            row["tones"] = s.get("tones", [])
        out.append(row)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
