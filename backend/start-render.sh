#!/usr/bin/env bash
set -eu

export ONNX_MODEL_DIR="${TMPDIR:-/tmp}/trash-onnx-model"
export ONNX_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export SMART_CROP="${SMART_CROP:-true}" U2NET_HOME="${U2NET_HOME:-$ONNX_MODEL_DIR}"

python -m onnx_fp32.render_model model-parts "$ONNX_MODEL_DIR" /etc/secrets/onnx-model-key
exec python -m uvicorn onnx_fp32.render_app:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 1
