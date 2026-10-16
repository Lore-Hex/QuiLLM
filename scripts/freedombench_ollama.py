#!/usr/bin/env python3
"""Run the pinned FreedomBench questions against local, hash-verified weights."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "benchmarks/freedombench/vendor"
sys.path.insert(0, str(VENDOR))
from freedombench.classify import extract_choice, summarize_results
from freedombench.questions import QUESTIONS, Question, rendered_options

UPSTREAM_COMMIT = "cc037ac7b286ba4f910309162367d856cbd25d58"
OPTIONS = {
    "temperature": 0.0, "seed": 16064, "num_ctx": 12288,
    "num_predict": 8192, "top_p": 1.0, "top_k": 0,
    "repeat_penalty": 1.0, "repeat_last_n": 64,
    "presence_penalty": 0.0, "frequency_penalty": 0.0,
    "stop": ["<|im_end|>", "<|endoftext|>", "<|im_start|>"],
}
TEMPLATE = (
    "<|im_start|>system\n{system}<|im_end|>\n"
    "<|im_start|>user\n{user}<|im_end|>\n"
    "<|im_start|>assistant\n<think>\n\n</think>\n\n"
)


def upstream_prompt_definitions():
    tree = ast.parse((VENDOR / "freedombench/run.py").read_text())
    system_node = next(n for n in tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "SYSTEM_PROMPT"
                               for t in n.targets))
    builder = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name == "build_prompt")
    namespace = {"Question": Question, "rendered_options": rendered_options}
    exec(compile(ast.Module(body=[builder], type_ignores=[]), "upstream/run.py", "exec"), namespace)
    return ast.literal_eval(system_node.value), namespace["build_prompt"]


SYSTEM_PROMPT, build_prompt = upstream_prompt_definitions()


def sha256_file(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def api(endpoint, path, payload=None):
    req = urllib.request.Request(
        endpoint.rstrip("/") + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as response:
        body = json.load(response)
    if body.get("error"):
        raise RuntimeError(body["error"])
    return body


def identify_model(endpoint, model):
    show = api(endpoint, "/api/show", {"model": model})
    match = re.search(r"^FROM\s+(.+)$", show["modelfile"], re.M)
    if not match:
        raise ValueError("Ollama did not expose a weight file for independent hashing")
    path = Path(match.group(1).strip().strip('"'))
    digest = sha256_file(path)
    if path.name.startswith("sha256-") and path.name != "sha256-" + digest:
        raise ValueError("Weight file does not match its content address")
    tags = api(endpoint, "/api/tags")["models"]
    tag = next(t for t in tags if t["name"] == model)
    return {
        "tag": model, "manifest_sha256": tag["digest"],
        "weight_sha256": digest, "weight_bytes": path.stat().st_size,
        "family": show["details"]["family"],
        "parameter_size": show["details"]["parameter_size"],
        "quantization": show["details"]["quantization_level"],
        "model_info": show.get("model_info", {}),
    }


def question_rows():
    rows = []
    for q in QUESTIONS:
        prompt, options, correct = build_prompt(q)
        rows.append({"id": q.id, "topic": q.topic, "question": q.question,
                     "options": options, "correct": correct, "source": q.source,
                     "prompt": prompt})
    return rows


def run_one(endpoint, model, question, call=api):
    row = {"model": model, "question_id": question["id"], "attempts": []}
    prompt = TEMPLATE.format(system=SYSTEM_PROMPT, user=question["prompt"])
    for _ in range(5):
        started = time.monotonic()
        try:
            result = call(endpoint, "/api/generate", {
                "model": model, "raw": True, "stream": False,
                "prompt": prompt, "options": OPTIONS, "keep_alive": "15m",
            })
            if not result.get("done") or not isinstance(result.get("response"), str):
                raise ValueError("Incomplete or malformed Ollama response")
            attempt = {key: result.get(key) for key in (
                "response", "done", "done_reason", "prompt_eval_count",
                "eval_count", "total_duration", "load_duration",
                "prompt_eval_duration", "eval_duration",
            )}
            attempt["wall_time_ms"] = round(1000 * (time.monotonic() - started))
            row["attempts"].append(attempt)
            row["output"] = result["response"]
            if extract_choice(row["output"]) is not None:
                break
        except Exception as exc:
            # Avoid recording endpoint paths or credentials in public error text.
            row["error"] = type(exc).__name__
            break
    row["empty_attempts"] = max(0, len(row["attempts"]) - 1)
    row["truncated_attempts"] = sum(a["done_reason"] == "length" for a in row["attempts"])
    return row


def summarize(report):
    expected = {q["id"] for q in report["questions"]}
    ids = [r["question_id"] for r in report["responses"]]
    if len(ids) != len(set(ids)) or not set(ids) <= expected:
        raise ValueError("Duplicate or unknown question IDs")
    rows = summarize_results(report)
    summary = rows[0] if rows else {}
    complete = set(ids) == expected and not summary.get("errors", 0)
    summary.update({
        "expected": len(expected), "complete": complete,
        "score_percent": round(100 * summary.get("correct", 0) / len(expected), 2) if complete else None,
        "truncated_attempts": sum(r.get("truncated_attempts", 0) for r in report["responses"]),
    })
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--source", required=True, help="Public weight source URL")
    parser.add_argument("--hardware", required=True, help="Public hardware description, not hostname")
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Result already exists; choose a new filename to preserve prior runs")
    identity = identify_model(args.endpoint, args.model)
    if identity["weight_sha256"] != args.expected_sha256:
        parser.error("Model hash differs from the explicitly selected weights")
    report = {
        "benchmark": "FreedomBench", "version": "1.0.2",
        "upstream_commit": UPSTREAM_COMMIT,
        "source_hashes": {str(p.relative_to(VENDOR)): sha256_file(p)
                          for p in sorted(VENDOR.rglob("*.py"))},
        "runner_sha256": sha256_file(__file__),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "label": args.label, "weight_source": args.source,
        "model_identity": identity, "models": [args.model],
        "runtime": {"ollama": api(args.endpoint, "/api/version")["version"],
                    "python": platform.python_version(), "os": platform.system(),
                    "os_release": platform.release(), "machine": platform.machine(),
                    "hardware": args.hardware},
        "system_prompt": SYSTEM_PROMPT, "raw_template": TEMPLATE,
        "options": OPTIONS, "thinking": False, "concurrency": 1,
        "maximum_attempts_per_question": 5,
        "questions": question_rows(), "responses": [],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for q in report["questions"]:
        row = run_one(args.endpoint, args.model, q)
        report["responses"].append(row)
        report["summary"] = summarize(report)
        # Atomic checkpoints preserve all completed answers after interruption.
        temporary = args.out.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        temporary.replace(args.out)
        choice = extract_choice(row.get("output", ""))
        status = "error" if row.get("error") else "correct" if choice == q["correct"] else "no_choice" if choice is None else "incorrect"
        print(f"{len(report['responses'])}/60 {q['id']}: {status}", flush=True)
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
