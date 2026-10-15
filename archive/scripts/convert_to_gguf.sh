#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR=""
NAME="QuiLLMv1-1.7B"
LLAMA_CPP="${LLAMA_CPP:-}"
OUT_DIR="$ROOT/dist"
PYTHON_BIN="${PYTHON:-python3}"
BUILD_EXPERIMENTAL_Q3_Q4=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model-dir)
      MODEL_DIR="$2"
      shift 2
      ;;
    --name)
      NAME="$2"
      shift 2
      ;;
    --llama-cpp)
      LLAMA_CPP="$2"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --experimental-q3-q4)
      BUILD_EXPERIMENTAL_Q3_Q4=1
      shift
      ;;
    -h|--help)
      echo "Usage: $0 --model-dir outputs/QuiLLMv1-1.7B-hf [--name QuiLLMv1-1.7B] --llama-cpp /path/to/llama.cpp [--experimental-q3-q4]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$MODEL_DIR" || -z "$LLAMA_CPP" ]]; then
  echo "--model-dir and --llama-cpp are required" >&2
  exit 2
fi

if [[ ! -d "$MODEL_DIR" ]]; then
  echo "Missing model directory: $MODEL_DIR" >&2
  exit 1
fi

CONVERT="$LLAMA_CPP/convert_hf_to_gguf.py"
QUANTIZE="$LLAMA_CPP/build/bin/llama-quantize"

if [[ ! -f "$CONVERT" ]]; then
  echo "Missing llama.cpp converter: $CONVERT" >&2
  exit 1
fi

if [[ ! -x "$QUANTIZE" ]]; then
  echo "Missing llama.cpp quantizer: $QUANTIZE" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

F16="$OUT_DIR/${NAME}-f16.gguf"
Q5="$OUT_DIR/${NAME}-q5_k_m.gguf"

"$PYTHON_BIN" "$CONVERT" "$MODEL_DIR" --outfile "$F16" --outtype f16
"$QUANTIZE" "$F16" "$Q5" Q5_K_M

echo "Wrote:"
echo "  $F16"
echo "  $Q5"

if [[ "$BUILD_EXPERIMENTAL_Q3_Q4" -eq 1 ]]; then
  EXPERIMENTAL_DIR="$OUT_DIR/experimental/1.7b-q3-q4"
  mkdir -p "$EXPERIMENTAL_DIR"
  Q3="$EXPERIMENTAL_DIR/${NAME}-q3_k_m.gguf"
  Q4="$EXPERIMENTAL_DIR/${NAME}-q4_k_m.gguf"
  "$QUANTIZE" "$F16" "$Q3" Q3_K_M
  "$QUANTIZE" "$F16" "$Q4" Q4_K_M
  echo "Experimental only:"
  echo "  $Q3"
  echo "  $Q4"
fi
