"""Regenerate the article figures (PT and EN) into docs/figures/."""
import sys
from pathlib import Path
import graphviz
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
OUT = str(ROOT / "docs" / "figures")
sys.path.insert(0, str(ROOT))
BG = "#ffffff"; INK = "#20202e"; GREY = "#8d8d8d"
BLUE = "#3b5b92"; BLUEF = "#cddaeb"; GREEN = "#4a7c59"; GREENF = "#cbdccf"
RED = "#bf4f4a"; REDF = "#ecccc9"; AMBER = "#c98a2b"; AMBERF = "#eddcc0"
SOFT = "#f1efe8"

mpl.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 13,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK, "axes.grid": True,
    "grid.color": "#e3e1da", "grid.linewidth": 0.8, "axes.linewidth": 1.1,
})

T = {
 "pt": {
  "f1": dict(idea="ideia\n(1 linha)", sb="storyboard.py\nLLM local (Ollama)", shots="shots.json\n12 planos",
             rc="render_clips.py\nLTX-2.5", mlx="Mac: MLX\n(ltx-2-mlx)", comfy="Spark / GPU 24 GB:\nComfyUI (API)",
             clips="clips/*.mp4\nvídeo + som ambiente", last="último frame\n→ próximo plano", nar="narrate.py\nKokoro PT / EN",
             asm="assemble.py\nffmpeg: crossfade\n+ ducking", out="final_pt.mp4\nfinal_en.mp4", cont="continue: true"),
  "f2": dict(title="O mesmo tutorial, três máquinas",
             cols=["", "Mac M5 Max\n128 GB", "DGX Spark\n(GB10)", "PC com GPU\n24 GB"],
             rows=[["Memória", "128 GB unificada", "128 GB unificada", "24 GB VRAM\n+ 64 GB RAM (recom.)"],
                   ["Banda de memória", "614 GB/s", "273 GB/s", "936–1008 GB/s\n(3090 / 4090)"],
                   ["Stack", "MLX + Metal", "CUDA em ARM64", "CUDA em x86-64"],
                   ["Caminho do LTX-2.5", "ltx-2-mlx (CLI)", "ComfyUI + template", "ComfyUI + template"],
                   ["Pesos", "MLX int8\n(port comunitário)", "bf16 distilled\n(ou NVFP4)", "int8 convrot\n(só ComfyUI)"],
                   ["Onde quebra", "watchdog do Metal\nem frames longos", "block swap ligado\nderruba o tempo", "VRAM no limite:\num render por vez"]]),
  "f3": dict(title="Linha do tempo: 12 planos de 129 frames, crossfade de 0,4 s = 60,1 s",
             x="tempo no vídeo final (s)", v="vídeo", n="narração", t2v="plano novo (T2V)", i2v="continua do último frame (I2V)",
             ov="sobreposição\n0,4 s"),
  "f4": dict(title="Números publicados por terceiros (não é benchmark)",
             y="segundos de render por segundo de vídeo",
             labels=["M5 Max 128 GB\nLTX-2.5 Fast, MPS\n1024×576, 5 s", "RTX 3090 24 GB\nLTX-2.5 distilled\nComfyUI, 5 s",
                     "DGX Spark\nLTX-2.3 dev NVFP4\nComfyUI, 20 s"],
             proj="≈ {m:.0f} min\npara 60 s", note="Versões, resoluções e pipelines diferentes. Rode o bench_summary.py nas suas máquinas."),
 },
 "en": {
  "f1": dict(idea="idea\n(one line)", sb="storyboard.py\nlocal LLM (Ollama)", shots="shots.json\n12 shots",
             rc="render_clips.py\nLTX-2.5", mlx="Mac: MLX\n(ltx-2-mlx)", comfy="Spark / 24 GB GPU:\nComfyUI (API)",
             clips="clips/*.mp4\nvideo + ambient audio", last="last frame\n→ next shot", nar="narrate.py\nKokoro PT / EN",
             asm="assemble.py\nffmpeg: crossfade\n+ ducking", out="final_pt.mp4\nfinal_en.mp4", cont="continue: true"),
  "f2": dict(title="One tutorial, three machines",
             cols=["", "Mac M5 Max\n128 GB", "DGX Spark\n(GB10)", "PC with a\n24 GB GPU"],
             rows=[["Memory", "128 GB unified", "128 GB unified", "24 GB VRAM\n+ 64 GB RAM (rec.)"],
                   ["Memory bandwidth", "614 GB/s", "273 GB/s", "936–1008 GB/s\n(3090 / 4090)"],
                   ["Stack", "MLX + Metal", "CUDA on ARM64", "CUDA on x86-64"],
                   ["LTX-2.5 path", "ltx-2-mlx (CLI)", "ComfyUI + template", "ComfyUI + template"],
                   ["Weights", "MLX int8\n(community port)", "bf16 distilled\n(or NVFP4)", "int8 convrot\n(ComfyUI only)"],
                   ["Where it breaks", "Metal watchdog\non long clips", "block swap on\nkills speed", "VRAM at the edge:\none render at a time"]]),
  "f3": dict(title="Timeline: 12 shots of 129 frames, 0.4 s crossfade = 60.1 s",
             x="time in the final video (s)", v="video", n="narration", t2v="new shot (T2V)", i2v="continues from last frame (I2V)",
             ov="0.4 s\noverlap"),
  "f4": dict(title="Third-party published numbers (not a benchmark)",
             y="render seconds per second of video",
             labels=["M5 Max 128 GB\nLTX-2.5 Fast, MPS\n1024×576, 5 s", "RTX 3090 24 GB\nLTX-2.5 distilled\nComfyUI, 5 s",
                     "DGX Spark\nLTX-2.3 dev NVFP4\nComfyUI, 20 s"],
             proj="≈ {m:.0f} min\nfor 60 s", note="Different versions, resolutions and pipelines. Run bench_summary.py on your own machines."),
 }}


def fig1(lang):
    t = T[lang]["f1"]
    g = graphviz.Digraph(format="png")
    g.attr(rankdir="LR", bgcolor=BG, nodesep="0.45", ranksep="0.55", dpi="160", fontname="DejaVu Serif")
    g.attr("node", shape="box", style="rounded,filled", fontname="DejaVu Serif", fontsize="12",
           color=INK, penwidth="1.3", margin="0.18,0.12", fillcolor=SOFT, fontcolor=INK)
    g.attr("edge", color=INK, penwidth="1.3", fontname="DejaVu Serif", fontsize="10", fontcolor=INK)
    g.node("idea", t["idea"], fillcolor="white")
    g.node("sb", t["sb"], fillcolor=AMBERF, color=AMBER)
    g.node("shots", t["shots"], shape="note", fillcolor="white")
    g.node("rc", t["rc"], fillcolor=BLUEF, color=BLUE)
    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("mlx", t["mlx"], fillcolor="white", color=BLUE, style="rounded,dashed,filled")
        s.node("comfy", t["comfy"], fillcolor="white", color=BLUE, style="rounded,dashed,filled")
    g.node("clips", t["clips"], shape="folder", fillcolor="white")
    g.node("nar", t["nar"], fillcolor=GREENF, color=GREEN)
    g.node("asm", t["asm"], fillcolor=REDF, color=RED)
    g.node("out", t["out"], shape="box", fillcolor="white", color=RED, penwidth="2")
    g.edge("idea", "sb"); g.edge("sb", "shots"); g.edge("shots", "rc")
    g.edge("rc", "mlx", arrowhead="none", style="dashed", color=BLUE)
    g.edge("rc", "comfy", arrowhead="none", style="dashed", color=BLUE)
    g.edge("mlx", "clips"); g.edge("comfy", "clips")
    g.edge("clips", "rc", label=t["cont"], style="dashed", color=GREY, fontcolor=GREY, constraint="false")
    g.edge("shots", "nar", color=GREEN)
    g.edge("clips", "asm"); g.edge("nar", "asm", color=GREEN); g.edge("asm", "out", color=RED)
    g.render(f"{OUT}/fig1_pipeline_{lang}", cleanup=True)


def fig2(lang):
    t = T[lang]["f2"]
    cols, rows = t["cols"], t["rows"]
    fig, ax = plt.subplots(figsize=(12.5, 6.6), layout="constrained")
    ax.axis("off"); ax.grid(False)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    x0 = [0, 22, 48, 74]; w = [21, 25, 25, 26]
    head_h = 13; row_h = 13.4; top = 92
    ax.text(0, 99, t["title"], fontsize=17, fontweight="bold", va="top")
    fills = [None, BLUEF, GREENF, AMBERF]
    edges = [None, BLUE, GREEN, AMBER]
    for j, c in enumerate(cols):
        if j == 0:
            continue
        ax.add_patch(FancyBboxPatch((x0[j] + 0.4, top - head_h), w[j] - 0.8, head_h - 1,
                                    boxstyle="round,pad=0,rounding_size=1.2", fc=fills[j], ec=edges[j], lw=1.4))
        ax.text(x0[j] + w[j] / 2, top - head_h / 2 - 0.5, c, ha="center", va="center", fontsize=13.5, fontweight="bold")
    for i, r in enumerate(rows):
        y = top - head_h - (i + 1) * row_h
        if i % 2 == 0:
            ax.add_patch(FancyBboxPatch((0, y + 0.3), 100, row_h - 0.6, boxstyle="round,pad=0,rounding_size=0.8",
                                        fc=SOFT, ec="none"))
        for j, cell in enumerate(r):
            if j == 0:
                ax.text(x0[0] + 1, y + row_h / 2, cell, ha="left", va="center", fontsize=12.5, fontweight="bold")
            else:
                color = RED if i == len(rows) - 1 else INK
                ax.text(x0[j] + w[j] / 2, y + row_h / 2, cell, ha="center", va="center", fontsize=12, color=color,
                        linespacing=1.25)
    fig.savefig(f"{OUT}/fig2_maquinas_{lang}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig3(lang):
    t = T[lang]["f3"]
    import json
    from common import frames_for, shot_starts, total_length
    doc = json.load(open(ROOT / "examples" / "water_cycle.json", encoding="utf-8"))
    d = [frames_for(doc["seconds"]) / 24] * len(doc["shots"])
    st = shot_starts(d, 0.4); tot = total_length(d, 0.4)
    fig, ax = plt.subplots(figsize=(13.5, 4.6), layout="constrained")
    ax.grid(axis="y", visible=False)
    for i, (s, shot) in enumerate(zip(st, doc["shots"])):
        cont = shot["continue"]
        lane = 2.0 if i % 2 == 0 else 1.45
        ax.add_patch(FancyBboxPatch((s, lane), d[i], 0.42, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=GREENF if cont else BLUEF, ec=GREEN if cont else BLUE, lw=1.3))
        ax.text(s + d[i] / 2, lane + 0.21, str(shot["id"]), ha="center", va="center", fontsize=12, fontweight="bold")
        words = len(shot[f"narration_{lang}"].split())
        nd = min(words / 2.6, d[i] - 0.7)
        ax.add_patch(FancyBboxPatch((s + 0.25, 0.55), nd, 0.36, boxstyle="round,pad=0,rounding_size=0.1",
                                    fc=AMBERF, ec=AMBER, lw=1.1))
    # overlap callout between shot 1 and 2
    ov = st[1]
    ax.annotate(t["ov"], xy=(ov + 0.2, 1.92), xytext=(ov + 2.6, 2.75), fontsize=10.5, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=GREY, lw=1))
    ax.text(-0.6, 1.9, t["v"], ha="right", va="center", fontsize=12)
    ax.text(-0.6, 0.73, t["n"], ha="right", va="center", fontsize=12)
    ax.set_xlim(-0.2, tot + 0.4); ax.set_ylim(0.3, 3.15)
    ax.set_yticks([]); ax.set_xticks(range(0, 61, 5))
    for sp in ("left", "right", "top"):
        ax.spines[sp].set_visible(False)
    ax.set_xlabel(t["x"])
    ax.set_title(t["title"], fontsize=15, loc="left", pad=12)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=BLUEF, ec=BLUE, label=t["t2v"]), Patch(fc=GREENF, ec=GREEN, label=t["i2v"])],
              loc="upper right", bbox_to_anchor=(1.0, 1.0), ncol=2, frameon=False, fontsize=11)
    fig.savefig(f"{OUT}/fig3_timeline_{lang}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig4(lang):
    t = T[lang]["f4"]
    vals = [142.75 / 5.04, 150 / 5.0, 720 / 20.0]
    rendered = 12 * 129 / 24  # seconds of clips rendered for the 60.1 s cut
    fig, ax = plt.subplots(figsize=(11.5, 6.4), layout="constrained")
    cols = [BLUE, AMBER, GREEN]
    bars = ax.bar(range(3), vals, color=[BLUEF, AMBERF, GREENF], edgecolor=cols, linewidth=1.6, width=0.58)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.0, f"{v:.0f} s", ha="center", va="bottom", fontsize=14, fontweight="bold")
        ax.text(i, v / 2, t["proj"].format(m=v * rendered / 60), ha="center", va="center", fontsize=12, color=INK)
    ax.set_xticks(range(3)); ax.set_xticklabels(t["labels"], fontsize=11.5)
    ax.set_ylim(0, max(vals) * 1.22); ax.set_ylabel(t["y"])
    ax.grid(axis="x", visible=False)
    ax.set_title(t["title"], fontsize=15, loc="left", pad=12)
    fig.text(0.01, -0.02, t["note"], fontsize=10.5, color=GREY, ha="left", va="top")
    fig.savefig(f"{OUT}/fig4_numeros_terceiros_{lang}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


for lang in ("pt", "en"):
    fig1(lang); fig2(lang); fig3(lang); fig4(lang)
print("ok")
