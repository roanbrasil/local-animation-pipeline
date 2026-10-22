"""Render every shot of shots.json into clips/shot_XX.mp4 and log timings.

Mac (MLX):
  python render_clips.py --backend mlx --machine "M5 Max 128GB"
Spark or 24 GB GPU (ComfyUI running on :8188):
  python render_clips.py --backend comfy --machine "DGX Spark" \
      --t2v workflows/t2v_api.json --i2v workflows/i2v_api.json
"""
import argparse
import copy
import csv
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import requests

from common import frames_for, load_shots, probe_duration, snap32

LENGTH_KEYS = ("length", "num_frames", "frames_number")
SEED_KEYS = ("seed", "noise_seed")
TEXT_KEYS = ("text", "prompt")


def last_frame(video, png):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.25",
                    "-i", str(video), "-update", "1", "-q:v", "1", str(png)],
                   check=True)


def full_prompt(style, shot):
    return f"{shot['prompt']} {style}. Audio: {shot['audio']}."


# ---------------------------------------------------------------- MLX (Mac)
def render_mlx(a, prompt, frames, image, out):
    cmd = ["ltx-2-mlx", "generate", "--prompt", prompt, "--distilled",
           "-H", str(a.height), "-W", str(a.width), "-f", str(frames),
           "-s", str(a.seed), "--model", a.mlx_model, "-o", str(out)]
    if image:
        cmd += ["--image", str(image)]
    subprocess.run(cmd, check=True)


# --------------------------------------------------- ComfyUI (Spark, 24 GB)
def upload_image(url, path):
    with open(path, "rb") as f:
        r = requests.post(f"{url}/upload/image",
                          files={"image": (Path(path).name, f, "image/png")},
                          data={"overwrite": "true"}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return f"{j['subfolder']}/{j['name']}" if j.get("subfolder") else j["name"]


def patch_workflow(wf, prompt, frames, seed, image_name=None):
    """Patch an API-format workflow. Nodes are found by title (PROMPT,
    IMAGE) and by input name (length, seed). Returns the list of edits."""
    wf = copy.deepcopy(wf)
    edits = []
    for nid, node in wf.items():
        title = node.get("_meta", {}).get("title", "")
        ins = node.get("inputs", {})
        if title == "PROMPT":
            for k in TEXT_KEYS:
                if isinstance(ins.get(k), str):
                    ins[k] = prompt
                    edits.append(f"{nid}.{k}=<prompt>")
                    break
        if title == "IMAGE" and image_name:
            ins["image"] = image_name
            edits.append(f"{nid}.image={image_name}")
        for k in LENGTH_KEYS:
            if isinstance(ins.get(k), int):
                ins[k] = frames
                edits.append(f"{nid}.{k}={frames}")
        for k in SEED_KEYS:
            if isinstance(ins.get(k), int):
                ins[k] = seed
                edits.append(f"{nid}.{k}={seed}")
    if not any(".text=" in e or ".prompt=" in e for e in edits):
        raise SystemExit("no node titled PROMPT found in workflow")
    return wf, edits


def find_video(history):
    for node_out in history.get("outputs", {}).values():
        for items in node_out.values():
            if not isinstance(items, list):
                continue
            for it in items:
                if isinstance(it, dict) and str(it.get("filename", "")) \
                        .lower().endswith((".mp4", ".webm", ".mov")):
                    return it
    return None


def render_comfy(a, prompt, frames, image, out):
    wf_path = a.i2v if image else a.t2v
    with open(wf_path, encoding="utf-8") as f:
        wf = json.load(f)
    name = upload_image(a.comfy_url, image) if image else None
    wf, edits = patch_workflow(wf, prompt, frames, a.seed, name)
    if a.dry_run:
        print(f"  [dry-run] {wf_path}: " + ", ".join(edits))
        return False
    r = requests.post(f"{a.comfy_url}/prompt", timeout=60,
                      json={"prompt": wf, "client_id": str(uuid.uuid4())})
    r.raise_for_status()
    pid = r.json()["prompt_id"]
    while True:
        h = requests.get(f"{a.comfy_url}/history/{pid}", timeout=60).json()
        if pid in h:
            status = h[pid].get("status", {})
            if status.get("status_str") == "error":
                raise SystemExit(f"ComfyUI error: {status}")
            if status.get("completed", True):
                break
        time.sleep(2)
    vid = find_video(h[pid])
    if not vid:
        raise SystemExit("no video in ComfyUI outputs (is there a SaveVideo?)")
    r = requests.get(f"{a.comfy_url}/view", timeout=600, params={
        "filename": vid["filename"], "subfolder": vid.get("subfolder", ""),
        "type": vid.get("type", "output")})
    r.raise_for_status()
    Path(out).write_bytes(r.content)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="examples/water_cycle.json")
    ap.add_argument("--backend", choices=["mlx", "comfy"], required=True)
    ap.add_argument("--machine", default=os.uname().nodename)
    ap.add_argument("--out", default="clips")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=576)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--only", type=int, nargs="*", help="re-render these ids")
    ap.add_argument("--mlx-model", default="dgrauet/ltx-2.5-mlx-q8")
    ap.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    ap.add_argument("--t2v", default="workflows/t2v_api.json")
    ap.add_argument("--i2v", default="workflows/i2v_api.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    a.width, a.height = snap32(a.width), snap32(a.height)

    doc = load_shots(a.shots)
    out_dir = Path(a.out)
    out_dir.mkdir(exist_ok=True)
    frames = frames_for(doc.get("seconds", 5.5))
    log = out_dir / "timings.csv"
    new_log = not log.exists()
    render = render_mlx if a.backend == "mlx" else render_comfy

    with open(log, "a", newline="") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(["machine", "backend", "shot", "width", "height",
                        "frames", "clip_s", "wall_s", "s_per_video_s"])
        prev = None
        for shot in doc["shots"]:
            clip = out_dir / f"shot_{shot['id']:02d}.mp4"
            image = None
            if shot.get("continue") and prev and prev.exists():
                image = out_dir / f"shot_{shot['id']:02d}_start.png"
                last_frame(prev, image)
            if a.only and shot["id"] not in a.only:
                prev = clip
                continue
            print(f"shot {shot['id']:02d} ({'i2v' if image else 't2v'}) "
                  f"{a.width}x{a.height} {frames} frames")
            t0 = time.perf_counter()
            done = render(a, full_prompt(doc["style"], shot), frames,
                          image, clip)
            wall = time.perf_counter() - t0
            if done is not False:
                clip_s = probe_duration(clip)
                w.writerow([a.machine, a.backend, shot["id"], a.width,
                            a.height, frames, f"{clip_s:.2f}", f"{wall:.1f}",
                            f"{wall / clip_s:.1f}"])
                f.flush()
                print(f"  {wall:.0f}s wall, {wall / clip_s:.1f}s per "
                      f"second of video")
            prev = clip


if __name__ == "__main__":
    main()
