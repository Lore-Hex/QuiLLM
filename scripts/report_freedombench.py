#!/usr/bin/env python3
"""Recompute FreedomBench tables from the four completed Beelink runs."""

import argparse
import csv
import io
import json

from freedombench_ollama import ROOT, extract_choice, summarize

DIRECTORY = ROOT / "reports/freedombench/2026-10-16"
NAMES = ["qwen3-1.7b", "quillm-1.7b", "qwen3-4b", "quillm-4b"]


def render(directory=DIRECTORY):
    reports = {name: json.loads((directory / f"{name}.json").read_text()) for name in NAMES}
    first = reports[NAMES[0]]
    for report in reports.values():
        if not summarize(report)["complete"] or summarize(report) != report["summary"]:
            raise ValueError("All four runs must be complete, correctly scored and error-free")
        for key in ("questions", "source_hashes", "options", "raw_template", "system_prompt", "runner_sha256", "runtime"):
            if report[key] != first[key]:
                raise ValueError(f"Mismatched comparison setting: {key}")
    lines = [
        "# FreedomBench local comparison: October 16, 2026", "",
        "Generated from all 240 Beelink answers using the unchanged FreedomBench scorer.", "",
        "| Model | Quantization | Correct / 60 | Score | Incorrect choice | No parsed choice | Errors |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for name, report in reports.items():
        s = report["summary"]
        lines.append(f"| [{report['label']}]({name}.json) | {report['model_identity']['quantization']} | "
                     f"{s['correct']} / 60 | {s['score_percent']:.2f}% | {s['incorrect']} | {s['refused']} | {s['errors']} |")
    lines += ["", "The upstream scorer calls answers without a parsed A-D choice `refused`.",
              "That includes prose and formatting failures, not only actual refusals.",
              "These are benchmark scores, not general factuality or safety scores.", "", "## Paired changes", "",
              "| Size | QuiLLM minus Qwen | Newly correct | Newly missed | Both correct | Both missed |",
              "|---|---:|---:|---:|---:|---:|"]
    correct = {q["id"]: q["correct"] for q in first["questions"]}
    for size in ("1.7b", "4b"):
        base, modified = reports[f"qwen3-{size}"], reports[f"quillm-{size}"]
        a = {r["question_id"]: extract_choice(r["output"]) == correct[r["question_id"]] for r in base["responses"]}
        b = {r["question_id"]: extract_choice(r["output"]) == correct[r["question_id"]] for r in modified["responses"]}
        gained = sum(b[q] and not a[q] for q in correct)
        lost = sum(a[q] and not b[q] for q in correct)
        both = sum(a[q] and b[q] for q in correct)
        neither = sum(not a[q] and not b[q] for q in correct)
        delta = (sum(b.values()) - sum(a.values())) * 100 / 60
        lines.append(f"| {size.upper()} | {delta:+.2f} percentage points | {gained} | {lost} | {both} | {neither} |")
    lines += ["", "## Topic scores", "", "| Topic | Qwen 1.7B | QuiLLM 1.7B | Qwen 4B | QuiLLM 4B |",
              "|---|---:|---:|---:|---:|"]
    for topic in sorted({q["topic"] for q in first["questions"]}):
        scores = [str(reports[n]["summary"]["by_topic"][topic]) + " / 5" for n in NAMES]
        lines.append("| " + topic + " | " + " | ".join(scores) + " |")
    lines += ["", "## Execution", "", "| Model | Requests including retries | Output tokens | Truncated attempts |",
              "|---|---:|---:|---:|"]
    for report in reports.values():
        attempts = [a for r in report["responses"] for a in r["attempts"]]
        lines.append(f"| {report['label']} | {len(attempts)} | {sum(a['eval_count'] for a in attempts)} | {report['summary']['truncated_attempts']} |")
    lines += ["", "All inference ran locally, with no paid inference API or judge calls.",
              "Electricity and existing hardware costs are not measured.", "",
              "[Methodology, interpretation and reproduction](../../../docs/FREEDOMBENCH.md)", ""]
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["model", "question_id", "topic", "correct_letter", "selected_letter", "outcome", "attempts", "truncated_attempts"])
    for report in reports.values():
        topics = {q["id"]: q["topic"] for q in report["questions"]}
        for row in report["responses"]:
            qid = row["question_id"]
            selected = extract_choice(row["output"])
            outcome = "no_choice" if selected is None else "correct" if selected == correct[qid] else "incorrect"
            writer.writerow([report["label"], qid, topics[qid], correct[qid], selected or "", outcome,
                             len(row["attempts"]), row["truncated_attempts"]])
    return {"README.md": "\n".join(lines), "answers.csv": output.getvalue()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, text in render().items():
        path = DIRECTORY / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit(f"Report differs: {name}")
        else:
            path.write_text(text)
    print("FreedomBench tables match saved answers." if args.check else "Wrote FreedomBench tables.")


if __name__ == "__main__":
    main()
