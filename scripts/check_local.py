#!/usr/bin/env python3
"""Run local regression checks; raw reports remain local until reviewed."""
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=["quillm:4b-sft8-q4", "quillm:sft4-q5"])
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with urllib.request.urlopen(args.endpoint.rstrip("/") + "/api/version", timeout=10) as response:
        version = json.load(response)
    (args.output_dir / "runtime.json").write_text(json.dumps(version, indent=2) + "\n")
    results = []
    for model in args.models:
        for probe in ["political_probe", "safety_preserve_probe", "recovery_probe_20261015"]:
            name = model.replace(":", "-").replace("/", "-") + "-" + probe
            command = [sys.executable, str(ROOT / "scripts/evaluate_ollama.py"), "--model", model,
                       "--endpoint", args.endpoint, "--probe", f"evals/{probe}.jsonl", "--report", str(args.output_dir / (name + ".json"))]
            completed = subprocess.run(command, cwd=ROOT, check=False)
            results.append({"model": model, "probe": probe, "exit_code": completed.returncode})
            if completed.returncode not in (0, 1):
                (args.output_dir / "suite.json").write_text(json.dumps(results, indent=2) + "\n")
                return 2
    (args.output_dir / "suite.json").write_text(json.dumps(results, indent=2) + "\n")
    return int(any(row["exit_code"] != 0 for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
