# CPU-only sentiment & tone — no Torch/Transformers to avoid meta-device issues on Windows.
# Uses VADER polarity + simple keyword heuristics for tones (sad / annoyed / doubtful, etc.).

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

_analyzer = SentimentIntensityAnalyzer()

# simple phrase lists for tone tagging (extend as you like)
TONE_PATTERNS = {
    "doubtful": [
        r"\b(i\s*guess|maybe|perhaps|not\s*sure|unsure|uncertain|i\s*think\s*so|probably|possibly)\b",
        r"\b(doubt|doubtful|skeptical|hesitant)\b",
        r"\?\s*$",  # trailing question tone
    ],
    "annoyed": [
        r"\b(annoyed|annoying|irritated|irritating|frustrated|frustrating|fed\s*up|sick\s*of)\b",
        r"\b(ugh+|grr+|ffs)\b",
        r"!{2,}",  # multiple exclamation marks
    ],
    "sad": [
        r"\b(sad|upset|depressed|unhappy|heartbroken|miserable|downcast)\b",
        r"\b(sorry|regret|regretting|mourning|grieving)\b",
        r"😢|😭|☹️|🙁",
    ],
    "angry": [
        r"\b(angry|mad|furious|livid|rage|enraged|outraged)\b",
        r"🤬|😡",
    ],
    "confident": [
        r"\b(definitely|certainly|for\s*sure|no\s*doubt|clearly|obviously)\b",
    ],
    "happy": [
        r"\b(happy|glad|pleased|delighted|thrilled|excited)\b",
        r"😊|😁|😄|🙂",
    ],
}

def _tone_tags(text: str) -> list[str]:
    if not text:
        return []
    tags = []
    t = text.lower()
    for label, patterns in TONE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, t, flags=re.IGNORECASE):
                tags.append(label)
                break
    # de-dup while preserving order
    seen = set()
    out = []
    for x in tags:
        if x not in seen:
            out.append(x); seen.add(x)
    # keep top 2
    return out[:2]

def label_text(text: str):
    txt = (text or "").strip()
    scores = _analyzer.polarity_scores(txt)
    compound = scores["compound"]
    # Map VADER compound to discrete label
    if compound >= 0.3:
        sent = "positive"
    elif compound <= -0.3:
        sent = "negative"
    else:
        sent = "neutral"
    tones = _tone_tags(txt)
    return {"sentiment": sent, "tones": tones}
