"""Make a YouTube-ready upload from the assembled cut.

  python youtube_export.py final_en.mp4 -o youtube/water_en_1080p.mp4

- upscales 1024x576 to 1920x1080 (lanczos), keeps 24 fps
- normalizes loudness to -14 LUFS, YouTube's playback target
- writes a 1280x720 thumbnail from a chosen second (--thumb-at)
"""
import argparse
import subprocess
from pathlib import Path

from common import probe_duration


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--thumb-at", type=float, default=27.0)
    a = ap.parse_args()

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", a.src,
        "-vf", f"scale={a.width}:{a.height}:flags=lanczos,format=yuv420p",
        "-r", "24", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-profile:v", "high", "-g", "48", "-bf", "2",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "384k", "-ar", "48000",
        "-movflags", "+faststart", str(out)], check=True)

    thumb = out.with_suffix(".jpg")
    at = min(a.thumb_at, max(0.0, probe_duration(out) - 0.5))
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-ss", str(at), "-i", str(out),
        "-frames:v", "1", "-vf", "scale=1280:720", "-q:v", "2", str(thumb)],
        check=True)
    print(f"wrote {out} ({probe_duration(out):.2f}s) and {thumb}")


if __name__ == "__main__":
    main()
