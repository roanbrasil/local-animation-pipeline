"""Turn a one-line idea into shots.json using a local LLM served by Ollama.

usage:
  python storyboard.py "the water cycle told by a single drop" -o shots.json
  python storyboard.py --check shots.json      # validate a hand-written file
"""
import argparse
import json
import sys

import requests

from common import FPS, frames_for

WORDS_PER_SECOND = 2.4   # comfortable narration pace, PT and EN
FADE = 0.4

SCHEMA = {
    "type": "object",
    "required": ["title", "style", "shots"],
    "properties": {
        "title": {"type": "string"},
        "style": {"type": "string"},
        "shots": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "continue", "prompt", "audio",
                             "narration_pt", "narration_en"],
                "properties": {
                    "id": {"type": "integer"},
                    "continue": {"type": "boolean"},
                    "prompt": {"type": "string"},
                    "audio": {"type": "string"},
                    "narration_pt": {"type": "string"},
                    "narration_en": {"type": "string"},
                },
            },
        },
    },
}

SYSTEM = """You are a storyboard writer for short AI-generated films.
Write exactly {n} shots of about {sec} seconds each for a one-minute film.
Rules:
- "prompt": English, one or two sentences, ONE camera move and ONE action. Describe what is visible, never what is felt.
- "continue": true only when the shot is the direct physical continuation of the previous one (same place, same subject).
- "audio": ambient sound only, no music, no speech.
- "narration_pt" and "narration_en": at most {words} words each, one sentence, same meaning.
- "style": one line shared by every shot (look, light, lens).
- Avoid human faces and readable text on screen."""


def validate(doc, n=None, seconds=5.5):
    errors = []
    shots = doc.get("shots", [])
    if n is not None and len(shots) != n:
        errors.append(f"expected {n} shots, got {len(shots)}")
    if shots and shots[0].get("continue"):
        errors.append("shot 1 cannot continue a previous shot")
    clip = frames_for(seconds) / FPS
    max_words = int((clip - FADE) * WORDS_PER_SECOND)
    for s in shots:
        for lang in ("narration_pt", "narration_en"):
            w = len(s.get(lang, "").split())
            if w > max_words:
                errors.append(f"shot {s.get('id')}: {lang} has {w} words "
                              f"(max {max_words})")
    return errors


def generate(idea, n, seconds, model, host):
    words = int((frames_for(seconds) / FPS - FADE) * WORDS_PER_SECOND)
    system = SYSTEM.format(n=n, sec=seconds, words=words)
    r = requests.post(f"{host}/api/chat", timeout=600, json={
        "model": model,
        "stream": False,
        "format": SCHEMA,
        "options": {"temperature": 0.4},
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": idea}],
    })
    r.raise_for_status()
    doc = json.loads(r.json()["message"]["content"])
    doc["seconds"] = seconds
    for i, s in enumerate(doc["shots"], start=1):
        s["id"] = i
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idea", nargs="?")
    ap.add_argument("-o", "--out", default="shots.json")
    ap.add_argument("-n", "--shots", type=int, default=12)
    ap.add_argument("-s", "--seconds", type=float, default=5.5)
    ap.add_argument("--model", default="qwen2.5:14b")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--check")
    a = ap.parse_args()

    if a.check:
        with open(a.check, encoding="utf-8") as f:
            doc = json.load(f)
        errs = validate(doc, seconds=doc.get("seconds", a.seconds))
        print("\n".join(errs) or "ok")
        sys.exit(1 if errs else 0)

    for attempt in range(3):
        doc = generate(a.idea, a.shots, a.seconds, a.model, a.host)
        errs = validate(doc, a.shots, a.seconds)
        if not errs:
            break
        print(f"attempt {attempt + 1}: " + "; ".join(errs), file=sys.stderr)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"wrote {a.out}" + (" (with warnings)" if errs else ""))


if __name__ == "__main__":
    main()
