"""Generate the narration track with Kokoro, aligned to the shot timeline.

  python narrate.py --lang pt     # -> narration_pt.wav (voice pf_dora)
  python narrate.py --lang en     # -> narration_en.wav (voice af_heart)
"""
import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

from common import (FPS, frames_for, load_shots, probe_duration, shot_starts,
                    total_length)

SR = 24000
VOICES = {"pt": ("p", "pf_dora"), "en": ("a", "af_heart")}


def place_segments(segments, starts, total_s, sr=SR, lead_in=0.25):
    """Lay each narration segment at its shot start (+ lead_in).
    Returns the full track and a list of overflow warnings."""
    track = np.zeros(int(round(total_s * sr)) + sr, dtype=np.float32)
    warnings = []
    for i, (seg, t) in enumerate(zip(segments, starts)):
        if seg is None or len(seg) == 0:
            continue
        begin = int(round((t + lead_in) * sr))
        limit = int(round(starts[i + 1] * sr)) if i + 1 < len(starts) \
            else len(track)
        end = begin + len(seg)
        if end > limit:
            warnings.append(f"shot {i + 1}: narration overflows by "
                            f"{(end - limit) / sr:.2f}s")
        end = min(end, len(track))
        track[begin:end] += seg[: end - begin]
    peak = float(np.max(np.abs(track))) or 1.0
    return track[: int(round(total_s * sr))] / max(peak, 1.0), warnings


def synth(pipeline, text, voice, speed):
    parts = [np.asarray(audio, dtype=np.float32)
             for _, _, audio in pipeline(text, voice=voice, speed=speed)]
    return np.concatenate(parts) if parts else np.zeros(0, np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="examples/water_cycle.json")
    ap.add_argument("--clips", default="clips")
    ap.add_argument("--lang", choices=["pt", "en"], default="pt")
    ap.add_argument("--voice")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--fade", type=float, default=0.4)
    a = ap.parse_args()

    from kokoro import KPipeline  # imported here so --help works without it

    doc = load_shots(a.shots)
    lang_code, default_voice = VOICES[a.lang]
    voice = a.voice or default_voice
    pipeline = KPipeline(lang_code=lang_code)

    durations = []
    for s in doc["shots"]:
        clip = Path(a.clips) / f"shot_{s['id']:02d}.mp4"
        durations.append(probe_duration(clip) if clip.exists()
                         else frames_for(doc.get("seconds", 5.5)) / FPS)
    starts = shot_starts(durations, a.fade)
    total = total_length(durations, a.fade)

    segments = [synth(pipeline, s[f"narration_{a.lang}"], voice, a.speed)
                for s in doc["shots"]]
    track, warns = place_segments(segments, starts, total)
    for w in warns:
        print("warning:", w, "-> shorten the line or raise --speed")
    out = f"narration_{a.lang}.wav"
    sf.write(out, track, SR)
    print(f"wrote {out} ({total:.2f}s)")


if __name__ == "__main__":
    main()
