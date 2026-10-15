#!/usr/bin/env python3
"""Verify local JSONL datasets load with Hugging Face datasets."""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--split", default="train")
    parser.add_argument("--column", default="text")
    args = parser.parse_args()

    dataset = load_dataset(str(args.dataset_dir), split=args.split)
    print(f"rows={len(dataset)} columns={dataset.column_names}")
    if args.column not in dataset.column_names:
        raise SystemExit(f"missing column: {args.column}")
    print(dataset[0][args.column])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

