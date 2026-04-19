#!/usr/bin/env bash
# Minimal wrapper around Kohya_ss SDXL LoRA training.
# Run this from the 03-lora directory after editing kohya-config.toml.

set -euo pipefail

KOHYA_DIR="${KOHYA_DIR:-$HOME/kohya_ss}"
CONFIG="${CONFIG:-$(pwd)/kohya-config.toml}"

if [[ ! -d "$KOHYA_DIR" ]]; then
  echo "Kohya_ss not found at $KOHYA_DIR"
  echo "Clone it first: git clone https://github.com/bmaltais/kohya_ss $KOHYA_DIR"
  exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Config not found: $CONFIG"
  exit 1
fi

# Guard against running with unfilled <tune> placeholders
if grep -q '<tune>' "$CONFIG"; then
  echo "Config still contains <tune> placeholders. Fill them in first."
  exit 1
fi

cd "$KOHYA_DIR"
exec accelerate launch --num_cpu_threads_per_process 4 \
  sdxl_train_network.py \
  --config_file "$CONFIG"
