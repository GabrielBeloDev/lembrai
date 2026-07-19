#!/usr/bin/env bash
# Local LoRA fine-tuning of a small 4-bit model to the "lembrai" answer style.
# Runs on Apple Silicon via MLX, in a dedicated venv (not the product's .venv).
# Override any knob from the environment, e.g. ITERS=400 ./run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LORA="$HERE/.venv-mlx/bin/mlx_lm.lora"

MODEL="${MODEL:-mlx-community/Qwen2.5-0.5B-Instruct-4bit}"
DATA="$HERE/data"
ADAPTERS="$HERE/adapters"
ITERS="${ITERS:-120}"
BATCH_SIZE="${BATCH_SIZE:-4}"
NUM_LAYERS="${NUM_LAYERS:-8}"
LEARNING_RATE="${LEARNING_RATE:-5e-5}"
MAX_SEQ_LENGTH="${MAX_SEQ_LENGTH:-512}"

"$LORA" \
  --model "$MODEL" \
  --train \
  --data "$DATA" \
  --fine-tune-type lora \
  --num-layers "$NUM_LAYERS" \
  --batch-size "$BATCH_SIZE" \
  --iters "$ITERS" \
  --learning-rate "$LEARNING_RATE" \
  --max-seq-length "$MAX_SEQ_LENGTH" \
  --mask-prompt \
  --steps-per-report 10 \
  --steps-per-eval 50 \
  --val-batches 3 \
  --adapter-path "$ADAPTERS" \
  --seed 42
