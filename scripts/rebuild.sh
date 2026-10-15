#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SIZE="${1:-}"
case "$SIZE" in
  1.7b)
    BASE=Qwen3-1.7B
    REV=70d244cc86ccca08cf5af4e1e306ecf908b1ad5e
    JOURNAL=runs/qwen3_1_7b_opi/checkpoints/models--base--Qwen3-1--7B.jsonl
    TRIAL=80
    EPOCHS=4
    NAME=QuiLLMv1-1.7B
    QUANT=Q5_K_M
    ;;
  4b)
    BASE=Qwen3-4B
    REV=1cfa9a7208912126459214e8b04321603b3df60c
    JOURNAL=runs/qwen3_4b_azulle/checkpoints/models--base--Qwen3-4B.jsonl
    TRIAL=4
    EPOCHS=8
    NAME=QuiLLMv1-4B
    QUANT=Q4_K_M
    ;;
  *) echo "Usage: bash scripts/rebuild.sh 1.7b|4b" >&2; exit 2 ;;
esac
LLAMA_CPP="${LLAMA_CPP:-tools/llama.cpp}"
QUANT_LOWER="$(printf '%s' "$QUANT" | tr '[:upper:]' '[:lower:]')"
if [[ -e "outputs/$NAME-rebuild-abliterated" || -e "outputs/$NAME-rebuild-calibrated" || -e "dist/$NAME-$QUANT_LOWER.gguf" || -e "dist/$NAME-rebuild-f16.gguf" ]]; then
  echo "A rebuild output already exists. Use a fresh checkout to preserve previous work." >&2
  exit 1
fi
if [[ ! -x "$LLAMA_CPP/build/bin/llama-quantize" ]]; then
  echo "Build the pinned llama.cpp first; see docs/REPRODUCE.md" >&2
  exit 1
fi
hf download "Qwen/$BASE" --revision "$REV" --local-dir "models/base/$BASE"
python scripts/export_heretic_trial.py --checkpoint "$JOURNAL" --trial-index "$TRIAL" --output-dir "outputs/$NAME-rebuild-abliterated"
python scripts/sft_calibrate.py --base-model "outputs/$NAME-rebuild-abliterated" --epochs "$EPOCHS" --output-dir "outputs/$NAME-rebuild-calibrated"
mkdir -p dist
python "$LLAMA_CPP/convert_hf_to_gguf.py" "outputs/$NAME-rebuild-calibrated" --outfile "dist/$NAME-rebuild-f16.gguf" --outtype f16
"$LLAMA_CPP/build/bin/llama-quantize" "dist/$NAME-rebuild-f16.gguf" "dist/$NAME-$QUANT_LOWER.gguf" "$QUANT"
echo "Rebuilt weights. Run the probes and manually review answers before use."
