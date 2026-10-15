#!/usr/bin/env python3
"""Recompute public optimizer results without model dependencies or network access."""
import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_journal(path):
    trials = {}
    settings = None
    for row in rows(path):
        attributes = row.get("user_attr", {})
        if "settings" in attributes:
            settings = json.loads(attributes["settings"])
        if "trial_id" not in row:
            continue
        trial = trials.setdefault(row["trial_id"], {})
        trial.update(attributes)
        if row.get("op_code") == 6:
            for field in ("state", "values", "datetime_complete"):
                if field in row:
                    trial[field] = row[field]
    return settings, sorted((v for v in trials.values() if v.get("state") == 1), key=lambda t: t["index"])


def report():
    provenance = json.loads((ROOT / "models/provenance.json").read_text())
    result = {"meaning": "Heuristic optimizer scores before SFT/quantization, not independent benchmark accuracy.", "models": {}}
    csv_rows = []
    for name, model in provenance["models"].items():
        settings, trials = read_journal(ROOT / model["checkpoint"])
        selected = next(t for t in trials if t["index"] == model["trial_index"])
        result["models"][name] = {
            "completed_trials": len(trials), "configured_trials": settings["n_trials"],
            "selected_trial": selected,
        }
        for trial in trials:
            csv_rows.append({"model": name, **{k: trial.get(k) for k in ("index", "kl_divergence", "refusals", "base_refusals", "n_bad_prompts", "datetime_complete")}})
    result["dataset_counts"] = {str(p.relative_to(ROOT)): len(rows(p)) for p in sorted((ROOT / "datasets").rglob("*.jsonl"))}
    calibration = {r["prompt"].strip().casefold() for r in rows(ROOT / "datasets/calibration/quillmv1_sft.jsonl")}
    result["probe_overlap"] = {}
    for path in sorted((ROOT / "evals").glob("*.jsonl")):
        samples = rows(path)
        result["probe_overlap"][path.name] = {
            "total": len(samples),
            "exact_prompt_matches_in_calibration": sum(r["prompt"].strip().casefold() in calibration for r in samples),
            "note": "Exact string overlap only; paraphrases and shared topics can add further overlap.",
        }
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(csv_rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(csv_rows)
    return {"optimizer-summary.json": json.dumps(result, indent=2, ensure_ascii=False) + "\n", "optimizer-trials.csv": buffer.getvalue()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in report().items():
        path = ROOT / "reports" / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"Report differs: {name}. Run python3 scripts/summarize.py")
        else:
            path.parent.mkdir(exist_ok=True)
            with path.open("w", newline="") as output:
                output.write(content)
    print("Reports match the archived journals." if args.check else "Recomputed reports.")


if __name__ == "__main__":
    main()
