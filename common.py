"""Shared helpers: frame math, timeline math, ffprobe."""
import json
import subprocess

FPS = 24


def frames_for(seconds: float, fps: int = FPS) -> int:
    """LTX needs num_frames = 8k + 1. Return the closest valid count."""
    k = round((seconds * fps - 1) / 8)
    return max(1, 8 * k + 1)


def snap32(x: int) -> int:
    """LTX-2.5 needs width and height divisible by 32."""
    return max(32, int(round(x / 32)) * 32)


def xfade_offsets(durations, fade):
    """Offset (s) of each crossfade in the OUTPUT timeline.

    Transition i joins the stream built so far with clip i+1.
    It must start `fade` seconds before the stream ends.
    """
    offsets, t = [], 0.0
    for d in durations[:-1]:
        t += d - fade
        offsets.append(round(t, 4))
    return offsets


def shot_starts(durations, fade):
    """Start time (s) of every shot in the final video."""
    return [0.0] + xfade_offsets(durations, fade)


def total_length(durations, fade):
    return sum(durations) - fade * (len(durations) - 1)


def probe_duration(path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def has_audio(path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout
    return bool(out.strip())


def load_shots(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
