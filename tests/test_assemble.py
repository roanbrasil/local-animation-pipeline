"""End-to-end edit test with synthetic clips. Needs ffmpeg on PATH."""
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from common import probe_duration, shot_starts, total_length
from narrate import SR, place_segments
from render_clips import last_frame

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None,
                                reason="ffmpeg not installed")


def make_clip(path, with_audio, freq=440):
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
           "-i", "testsrc2=s=1024x576:r=24"]
    if with_audio:
        cmd += ["-f", "lavfi", "-i", f"sine=f={freq}:sample_rate=48000",
                "-t", "5.375", "-c:a", "aac", "-ac", "2"]
    cmd += ["-frames:v", "129", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(path)]
    subprocess.run(cmd, check=True)


def test_place_segments_warns_on_overflow():
    starts, total = [0.0, 5.0], 10.0
    seg = np.ones(int(6 * SR), np.float32) * 0.1
    track, warns = place_segments([seg, None], starts, total)
    assert len(track) == int(total * SR)
    assert warns and "shot 1" in warns[0]


def test_full_edit_is_sixty_seconds(tmp_path):
    clips = tmp_path / "clips"
    clips.mkdir()
    for i in range(1, 13):
        make_clip(clips / f"shot_{i:02d}.mp4", with_audio=(i != 5),
                  freq=200 + 40 * i)

    d = [probe_duration(p) for p in sorted(clips.glob("shot_??.mp4"))]
    t = np.arange(int(3 * SR)) / SR
    segs = [0.3 * np.sin(2 * np.pi * 440 * t).astype(np.float32)] * 12
    track, warns = place_segments(segs, shot_starts(d, 0.4),
                                  total_length(d, 0.4))
    assert warns == []
    narration = tmp_path / "narration_en.wav"
    sf.write(narration, track, SR)

    out = tmp_path / "final_en.mp4"
    subprocess.run([sys.executable, str(ROOT / "assemble.py"),
                    "--clips", str(clips), "--narration", str(narration),
                    "-o", str(out)], check=True)
    assert probe_duration(out) == pytest.approx(60.1, abs=0.1)

    png = tmp_path / "last.png"
    last_frame(clips / "shot_01.mp4", png)
    assert png.exists() and png.stat().st_size > 0
