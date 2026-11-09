#!/usr/bin/env bash
# Prepara as ferramentas de edição numa sessão nova (o computador na nuvem começa vazio).
# uso: ferramentas/instalar.sh <pasta_de_trabalho>   (ex.: a pasta scratchpad da sessão)
#  - venv3: Python com OpenCV, sherpa-onnx (Whisper sem GPU) e Pillow
#  - modelos: Whisper large-v3 (o mais preciso) e o VAD silero, dos releases do sherpa-onnx no GitHub
#    (o Hugging Face é bloqueado neste ambiente)
#  - Remotion (gráficos animados) usa o Chromium que já vem instalado em /opt/pw-browsers
set -euo pipefail
D=${1:?pasta de trabalho}
mkdir -p "$D/asr_models"
[ -x "$D/venv3/bin/python" ] || python3 -m venv --system-site-packages "$D/venv3"
"$D/venv3/bin/pip" install --quiet opencv-contrib-python-headless sherpa-onnx pillow
cd "$D/asr_models"
R=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
[ -f silero_vad.onnx ] || curl -sSLo silero_vad.onnx "$R/silero_vad.onnx"
if [ ! -f sherpa-onnx-whisper-large-v3/large-v3-tokens.txt ]; then
  curl -sSL "$R/sherpa-onnx-whisper-large-v3.tar.bz2" | tar xj
fi
echo "pronto: $D/venv3/bin/python e $D/asr_models/sherpa-onnx-whisper-large-v3"
