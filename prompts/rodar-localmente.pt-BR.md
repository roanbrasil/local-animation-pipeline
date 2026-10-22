# Prompt: renderizar o filme na sua própria máquina

Cole o bloco abaixo num agente de código rodando **na máquina que vai renderizar** (Claude Code no terminal, ou qualquer agente com acesso ao shell), a partir da raiz deste repositório. Ele detecta o hardware, escolhe o backend, renderiza, narra em PT e EN e deixa os arquivos prontos para o YouTube, junto com os metadados de upload.

Troque antes os dois marcadores: `<URL_ARTIGO_PT>` e `<URL_ARTIGO_EN>`.

---

```text
Você está rodando na máquina que vai renderizar um filme de IA de 60 segundos
com a pipeline deste repositório (leia o README.md primeiro). Trabalhe na raiz
do repo. Objetivo: dois vídeos prontos para o YouTube (narração PT e EN) de
examples/water_cycle.json, os metadados de upload e um relatório de tempos.

1. DETECTE A MÁQUINA e diga qual caminho escolheu antes de qualquer outra coisa:
   - macOS em Apple Silicon -> backend "mlx" (ltx-2-mlx, modelo dgrauet/ltx-2.5-mlx-q8)
   - Linux aarch64 com NVIDIA GB10 (DGX Spark) -> backend "comfy", pesos LTX-2.5 bf16
   - Linux ou Windows com GPU NVIDIA de 24 GB ou mais -> backend "comfy",
     pesos LTX-2.5 comfy-int8-convrot
   Informe: sistema, chip/GPU, memória/VRAM total, espaço livre em disco,
   versões de python e ffmpeg. Se faltar ffmpeg, python 3.11+ ou espeak-ng,
   me passe o comando exato de instalação e espere.

2. CONFIRME ANTES DE BAIXAR. Os pesos têm de 40 a 100 GB. Liste exatamente o
   que vai baixar, para onde e o tamanho total, e ESPERE meu "sim".
   Lightricks/LTX-2.5 é gated no Hugging Face: se `hf auth whoami` falhar ou
   o acesso for negado, pare e me peça para aceitar a licença e logar eu mesmo.
   Nunca cole nem guarde tokens.

3. MONTE o backend seguindo a seção do README para esta máquina.
   - mlx: clone dgrauet/ltx-2-mlx ao lado deste repo (não dentro), rode
     `uv sync --all-extras` e `ltx-2-mlx info --model dgrauet/ltx-2.5-mlx-q8`.
   - comfy: use um ComfyUI existente se responder em http://127.0.0.1:8188;
     senão instale o ComfyUI mais recente em ../ComfyUI (na Spark, torch do
     índice cu130). Confirme que os templates "LTX-2.5 T2V" e "LTX-2.5 I2V"
     existem; se não, o ComfyUI está desatualizado. Eu mesmo exporto
     workflows/t2v_api.json e workflows/i2v_api.json pela interface (README,
     "Exporting the ComfyUI workflows"); se faltarem, espere por mim, depois
     rode `python render_clips.py --backend comfy --dry-run --shots
     examples/water_cycle.json` e me mostre a lista de edições.

4. INSTALE as dependências deste repo num venv: `pip install -r
   requirements.txt -r requirements-narration.txt`. Rode `python -m pytest -q`
   e mostre o resultado. Não continue se algo falhar.

5. RENDERIZE SÓ O PLANO 1:
   python render_clips.py --backend <mlx|comfy> --shots examples/water_cycle.json \
     --machine "<nome curto da máquina>" --only 1 [--t2v workflows/t2v_api.json \
     --i2v workflows/i2v_api.json]
   Me diga o tempo de parede e o s-por-segundo-de-vídeo do clips/timings.csv,
   e o caminho de clips/shot_01.mp4, e ESPERE eu assistir.

6. RENDERIZE O RESTO (planos 2 a 12) com o mesmo comando, sem --only.
   Não mude seed, resolução nem o arquivo de planos. Se um plano falhar, tente
   de novo uma vez com --only N; se falhar outra vez, pare e me mostre o erro.
   No Mac, se aparecer erro de command buffer/watchdog do Metal, tente de novo
   com LTX2_DIT_EVAL_EVERY=4.

7. NARRE E MONTE:
   python narrate.py --shots examples/water_cycle.json --lang pt
   python narrate.py --shots examples/water_cycle.json --lang en
   python assemble.py --lang pt -o out/water_cycle_pt.mp4
   python assemble.py --lang en -o out/water_cycle_en.mp4
   Avise de qualquer "narration overflows"; se houver, rode de novo o
   narrate.py daquele idioma com --speed 1.1.

8. EXPORTE PARA O YOUTUBE:
   python youtube_export.py out/water_cycle_pt.mp4 -o youtube/water_cycle_pt_1080p.mp4
   python youtube_export.py out/water_cycle_en.mp4 -o youtube/water_cycle_en_1080p.mp4
   Confira com ffprobe: 1920x1080, 24 fps, ~60,1 s, áudio AAC.

9. ESCREVA youtube/metadata.md com, para cada idioma:
   - título com menos de 70 caracteres (o EN não é tradução literal do PT)
   - descrição que diga nas duas primeiras linhas que o filme foi gerado
     100% localmente em <máquina> com LTX-2.5 (vídeo + som ambiente) e Kokoro
     (narração), e depois o link do tutorial: PT -> <URL_ARTIGO_PT>,
     EN -> <URL_ARTIGO_EN>, e a URL do GitHub de `git remote get-url origin`,
     se houver
   - o tempo de render dos 12 planos, tirado do clips/timings.csv
   - de 8 a 12 tags
   - um lembrete de marcar SIM em "conteúdo alterado ou sintético" no upload
   Não suba nada. Eu faço o upload manualmente.

10. RELATÓRIO FINAL: máquina, backend, variante do modelo, minutos totais de
    render, s-por-segundo-de-vídeo, a saída de `python bench_summary.py
    clips/timings.csv` e os caminhos dos dois vídeos, das duas thumbnails e
    do metadata.md.

Regras: nunca rode sudo nem mude configurações do sistema sem perguntar; nunca
apague arquivos fora deste repo, de ../ltx-2-mlx e de ../ComfyUI; registre
todo comando que rodar em out/run_log.md para eu poder reproduzir.
```
