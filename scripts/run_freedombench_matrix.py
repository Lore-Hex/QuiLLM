#!/usr/bin/env python3
"""Run four fixed comparisons sequentially on the machine hosting Ollama."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from freedombench_ollama import OPTIONS, api, sha256_file, summarize

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--quillm4-tag", default="quillm:4b-q4_K_M")
    parser.add_argument("--quillm17-tag", default="freedombench-quillm:1.7b-q5_K_M")
    parser.add_argument("--qwen17-tag", default="freedombench-qwen3:1.7b-q5_K_M")
    parser.add_argument("--resume-complete", action="store_true",
                        help="Skip only complete, matching saved runs; never skip partial questions")
    args = parser.parse_args()
    runs = [
        ("qwen3:4b-q4_K_M", "Qwen3 4B (unmodified)",
         "https://ollama.com/library/qwen3:4b-q4_K_M",
         "163553aea1b1de62de7c5eb2ef5afb756b4b3133308d9ae7e42e951d8d696ef5", "qwen3-4b"),
        (args.quillm4_tag, "QuiLLMv1 4B",
         "https://github.com/Lore-Hex/QuiLLM/releases/tag/v1.0.0",
         "337ea93b7c8a99cebd818e8e80d1dcc39473b97a09164e2fa55c1b9cc0db4b8d", "quillm-4b"),
        (args.qwen17_tag, "Qwen3 1.7B (unmodified)",
         "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/tree/dcb19155b962dbb6389f4691a982043a8e651022",
         "4287aca1b231f27dbd20012c4bf9693c89b6c849dc02b7027096da54564d4037", "qwen3-1.7b"),
        (args.quillm17_tag, "QuiLLMv1 1.7B",
         "https://github.com/Lore-Hex/QuiLLM/releases/tag/v1.0.0",
         "a64125577d135a27c83e1f48e99516ffb13e0f3c3d2f330b950a0b5364dc22ed", "quillm-1.7b"),
    ]
    for model, label, source, digest, name in runs:
        destination = args.out / f"{name}.json"
        if args.resume_complete and destination.exists():
            report = json.loads(destination.read_text())
            if (not summarize(report)["complete"] or report["models"] != [model]
                    or report["model_identity"]["weight_sha256"] != digest
                    or report["options"] != OPTIONS
                    or report["runtime"]["hardware"] != args.hardware
                    or report["runner_sha256"] != sha256_file(ROOT / "scripts/freedombench_ollama.py")):
                raise ValueError(f"Cannot resume incomplete or mismatched run: {name}")
            print("COMPLETE", label, flush=True)
            api("http://127.0.0.1:11434", "/api/generate", {"model": model, "keep_alive": 0})
            continue
        print("START", label, flush=True)
        subprocess.run([
            sys.executable, str(ROOT / "scripts/freedombench_ollama.py"),
            "--hardware", args.hardware, "--model", model, "--label", label,
            "--source", source, "--expected-sha256", digest,
            "--out", str(destination),
        ], check=True)
        api("http://127.0.0.1:11434", "/api/generate", {"model": model, "keep_alive": 0})


if __name__ == "__main__":
    main()
