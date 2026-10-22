# Prompt: render the film on your own machine

Paste the block below into a coding agent running **on the machine that will render** (Claude Code in the terminal, or any agent with shell access), from the root of this repository. It detects the hardware, picks the backend, renders, narrates in PT and EN, and leaves YouTube-ready files plus upload metadata.

Replace the two placeholders first: `<ARTICLE_URL_PT>` and `<ARTICLE_URL_EN>`.

---

```text
You are running on the machine that will render a 60-second AI film with the
pipeline in this repository (read README.md first). Work from the repo root.
Goal: two YouTube-ready videos (PT and EN narration) of examples/water_cycle.json,
plus upload metadata, plus a timing report.

1. DETECT THE MACHINE and say which path you chose before doing anything else:
   - macOS on Apple Silicon -> backend "mlx" (ltx-2-mlx, model dgrauet/ltx-2.5-mlx-q8)
   - Linux aarch64 with an NVIDIA GB10 (DGX Spark) -> backend "comfy", bf16 LTX-2.5 weights
   - Linux or Windows with an NVIDIA GPU of 24 GB or more -> backend "comfy",
     comfy-int8-convrot LTX-2.5 weights
   Report: OS, chip/GPU, total memory/VRAM, free disk space, python and ffmpeg
   versions. If ffmpeg, python 3.11+ or espeak-ng is missing, tell me the exact
   install command and wait for me.

2. CHECK BEFORE DOWNLOADING. The model weights are 40-100 GB. List exactly what
   you will download, where, and the total size, then WAIT for my "yes".
   Lightricks/LTX-2.5 is gated on Hugging Face: if `hf auth whoami` fails or
   access is denied, stop and ask me to accept the license and log in myself.
   Never paste or store tokens.

3. SET UP the backend following the README section for this machine.
   - mlx: clone dgrauet/ltx-2-mlx next to this repo (not inside it), `uv sync
     --all-extras`, run `ltx-2-mlx info --model dgrauet/ltx-2.5-mlx-q8`.
   - comfy: use an existing ComfyUI if one answers on http://127.0.0.1:8188,
     otherwise install the latest ComfyUI in ../ComfyUI (on the Spark, torch
     from the cu130 index). Confirm the "LTX-2.5 T2V" and "LTX-2.5 I2V"
     templates exist; if not, ComfyUI is too old. I will export
     workflows/t2v_api.json and workflows/i2v_api.json from the UI myself
     (README, "Exporting the ComfyUI workflows"); wait for me if they are
     missing, then run `python render_clips.py --backend comfy --dry-run
     --shots examples/water_cycle.json` and show me the edit list.

4. INSTALL the Python deps of this repo in a venv: `pip install -r
   requirements.txt -r requirements-narration.txt`. Run `python -m pytest -q`
   and show the result. Do not continue on failures.

5. RENDER SHOT 1 ONLY:
   python render_clips.py --backend <mlx|comfy> --shots examples/water_cycle.json \
     --machine "<short machine name>" --only 1 [--t2v workflows/t2v_api.json \
     --i2v workflows/i2v_api.json]
   Tell me the wall time and the s-per-video-s from clips/timings.csv, and the
   path of clips/shot_01.mp4, then WAIT so I can watch it.

6. RENDER THE REST (shots 2-12) with the same command without --only.
   Do not change the seed, resolution or shots file. If a shot fails, retry it
   once with --only N; if it fails again, stop and show me the error.
   On a Mac, if you see a Metal command-buffer/watchdog error, retry with
   LTX2_DIT_EVAL_EVERY=4 set.

7. NARRATE AND ASSEMBLE:
   python narrate.py --shots examples/water_cycle.json --lang pt
   python narrate.py --shots examples/water_cycle.json --lang en
   python assemble.py --lang pt -o out/water_cycle_pt.mp4
   python assemble.py --lang en -o out/water_cycle_en.mp4
   Report any "narration overflows" warning; if any, rerun narrate.py with
   --speed 1.1 for that language only.

8. EXPORT FOR YOUTUBE:
   python youtube_export.py out/water_cycle_pt.mp4 -o youtube/water_cycle_pt_1080p.mp4
   python youtube_export.py out/water_cycle_en.mp4 -o youtube/water_cycle_en_1080p.mp4
   Verify with ffprobe: 1920x1080, 24 fps, ~60.1 s, AAC audio.

9. WRITE youtube/metadata.md with, for each language:
   - a title under 70 characters (PT: different title, not a literal translation)
   - a description that says in the first two lines the film was generated
     100% locally on <machine> with LTX-2.5 (video + ambient audio) and Kokoro
     (narration), then links the tutorial: PT -> <ARTICLE_URL_PT>,
     EN -> <ARTICLE_URL_EN>, and the GitHub repo URL from `git remote get-url origin`
     if there is one
   - the render time for the 12 shots, taken from clips/timings.csv
   - 8-12 tags
   - a reminder that YouTube's "altered or synthetic content" disclosure
     must be set to YES on upload
   Do not upload anything. I upload manually.

10. FINAL REPORT: machine, backend, model variant, total render minutes,
    s-per-video-s, the output of `python bench_summary.py clips/timings.csv`,
    and the paths of the two videos, the two thumbnails and metadata.md.

Rules: never run sudo or change system settings without asking; never delete
files outside this repo, ../ltx-2-mlx and ../ComfyUI; keep every command you
run in a log at out/run_log.md so I can reproduce it.
```
