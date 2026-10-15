#!/usr/bin/env python3
"""Export a selected Heretic trial from a checkpoint journal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

from heretic.config import Settings
from heretic.model import AbliterationParameters, Model
from heretic.system import empty_cache
from heretic.utils import load_prompts, set_seed


def load_study_settings(checkpoint: Path) -> Settings:
    settings_json = None
    with checkpoint.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            data = json.loads(line)
            attrs = data.get("user_attr") or {}
            if data.get("op_code") == 2 and "settings" in attrs:
                settings_json = attrs["settings"]
    if settings_json is None:
        raise SystemExit(f"No settings record found in {checkpoint}")
    return Settings.model_validate_json(settings_json)


def load_trial(checkpoint: Path, trial_index: int) -> tuple[float | None, dict[str, AbliterationParameters]]:
    trials: dict[int, dict] = {}
    with checkpoint.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            data = json.loads(line)
            trial_id = data.get("trial_id")
            if trial_id is None:
                continue
            trial = trials.setdefault(trial_id, {})
            if data.get("op_code") == 8:
                trial.update(data.get("user_attr") or {})
            elif data.get("op_code") == 6:
                trial["state"] = data.get("state")

    for trial in trials.values():
        if trial.get("index") != trial_index:
            continue
        if trial.get("state") != 1:
            raise SystemExit(f"Trial {trial_index} is not complete")
        params = {
            component: AbliterationParameters(**values)
            for component, values in trial["parameters"].items()
        }
        return trial.get("direction_index"), params

    raise SystemExit(f"Trial {trial_index} not found in {checkpoint}")


def compute_refusal_directions(settings: Settings, model: Model) -> torch.Tensor:
    print(f"Loading good prompts from {settings.good_prompts.dataset}...")
    good_prompts = load_prompts(settings, settings.good_prompts)
    print(f"Loading bad prompts from {settings.bad_prompts.dataset}...")
    bad_prompts = load_prompts(settings, settings.bad_prompts)

    print("Computing residual means...")
    good_means = model.get_residuals_mean(good_prompts)
    bad_means = model.get_residuals_mean(bad_prompts)
    refusal_directions = F.normalize(bad_means - good_means, p=2, dim=1)

    if settings.orthogonalize_direction:
        good_directions = F.normalize(good_means, p=2, dim=1)
        projection_vector = torch.sum(refusal_directions * good_directions, dim=1)
        refusal_directions = refusal_directions - projection_vector.unsqueeze(1) * good_directions
        refusal_directions = F.normalize(refusal_directions, p=2, dim=1)

    del good_means, bad_means
    empty_cache()
    return refusal_directions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--trial-index", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.argv = [sys.argv[0]]

    settings = load_study_settings(args.checkpoint)
    set_seed(settings.seed)

    direction_index, parameters = load_trial(args.checkpoint, args.trial_index)
    model = Model(settings)
    refusal_directions = compute_refusal_directions(settings, model)

    print(f"Applying trial {args.trial_index}...")
    model.abliterate(refusal_directions, direction_index, parameters)
    print("Saving merged model...")
    merged = model.get_merged_model()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(args.output_dir, max_shard_size=settings.max_shard_size)
    model.tokenizer.save_pretrained(args.output_dir)
    print(f"Wrote {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
