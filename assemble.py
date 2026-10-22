"""Join the clips with crossfades and mix the narration over the native audio.

  python assemble.py --lang pt -o agua_pt.mp4
  python assemble.py --lang en -o water_en.mp4
"""
import argparse
import subprocess
from pathlib import Path

from common import FPS, has_audio, probe_duration, xfade_offsets


def build_filter(n, durations, fade, width, height, audio_flags, amb_gain):
    v, a = [], []
    for i in range(n):
        v.append(f"[{i}:v]fps={FPS},scale={width}:{height},setsar=1,"
                 f"format=yuv420p,settb=AVTB[v{i}]")
        if audio_flags[i]:
            a.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo"
                     f"[a{i}]")
        else:
            a.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{durations[i]:.4f}"
                     f"[a{i}]")
    offs = xfade_offsets(durations, fade)
    vprev, aprev = "v0", "a0"
    for i in range(1, n):
        vo, ao = f"vx{i}", f"ax{i}"
        v.append(f"[{vprev}][v{i}]xfade=transition=fade:duration={fade}:"
                 f"offset={offs[i - 1]}[{vo}]")
        a.append(f"[{aprev}][a{i}]acrossfade=d={fade}[{ao}]")
        vprev, aprev = vo, ao
    narr = n  # narration is the input after the clips
    a.append(f"[{aprev}]volume={amb_gain}[amb]")
    a.append(f"[{narr}:a]aresample=48000,aformat=channel_layouts=stereo,"
             f"asplit=2[nar][key]")
    a.append("[amb][key]sidechaincompress=threshold=0.03:ratio=6:"
             "attack=20:release=500[duck]")
    a.append("[duck][nar]amix=inputs=2:duration=first:normalize=0,"
             "alimiter=limit=0.95[aout]")
    return ";".join(v + a), f"[{vprev}]", "[aout]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", default="clips")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--narration")
    ap.add_argument("--fade", type=float, default=0.4)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=576)
    ap.add_argument("--ambient-gain", type=float, default=0.6)
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    clips = sorted(Path(a.clips).glob("shot_[0-9][0-9].mp4"))
    if len(clips) < 2:
        raise SystemExit("need at least 2 clips in " + a.clips)
    narration = a.narration or f"narration_{a.lang}.wav"
    out = a.out or f"final_{a.lang}.mp4"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    durations = [probe_duration(c) for c in clips]
    audio_flags = [has_audio(c) for c in clips]
    graph, vmap, amap = build_filter(len(clips), durations, a.fade, a.width,
                                     a.height, audio_flags, a.ambient_gain)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += ["-i", narration, "-filter_complex", graph,
            "-map", vmap, "-map", amap,
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"wrote {out} ({probe_duration(out):.2f}s)")


if __name__ == "__main__":
    main()
