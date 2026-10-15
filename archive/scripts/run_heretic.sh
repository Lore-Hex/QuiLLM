#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/quillmv1-qwen3_1_7b-opi.toml"
MODEL=""
PRINT_RESPONSES="${PRINT_RESPONSES:-false}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --print-responses)
      PRINT_RESPONSES="true"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--config configs/file.toml] [--model HF_OR_LOCAL_MODEL] [--print-responses]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

cd "$ROOT"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing config: $CONFIG" >&2
  exit 1
fi

if [[ -e config.toml ]]; then
  echo "Refusing to overwrite existing $ROOT/config.toml" >&2
  echo "Move it aside or delete it before running." >&2
  exit 1
fi

cleanup() {
  rm -f "$ROOT/config.toml"
}
trap cleanup EXIT

cp "$CONFIG" config.toml

export HERETIC_PRINT_RESPONSES="$PRINT_RESPONSES"

if [[ -n "$MODEL" ]]; then
  heretic "$MODEL"
else
  heretic
fi
