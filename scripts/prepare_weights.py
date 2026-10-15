#!/usr/bin/env python3
"""Verify existing local Ollama blobs and create GitHub-sized release parts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PART_BYTES = 1_000_000_000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blob-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    provenance = json.loads((ROOT / "models/provenance.json").read_text())
    manifest = {"format": "gguf", "split": "Concatenate each model's parts in the given order.", "models": {}}
    for size, info in provenance["models"].items():
        source = args.blob_dir / ("sha256-" + info["weight_sha256"])
        if source.stat().st_size != info["weight_bytes"]:
            raise SystemExit(f"Size mismatch for {size}")
        digest = hashlib.sha256()
        parts = []
        with source.open("rb") as reader:
            number = 0
            while True:
                chunk = reader.read(8 * 1024 * 1024)
                if not chunk:
                    break
                name = f"QuiLLMv1-{size.upper()}-{info['quantization'].lower()}.gguf.part{number:02d}"
                number += 1
                remaining = PART_BYTES
                part_hash = hashlib.sha256()
                part_bytes = 0
                with (args.output_dir / name).open("xb") as writer:
                    while chunk:
                        writer.write(chunk)
                        digest.update(chunk)
                        part_hash.update(chunk)
                        part_bytes += len(chunk)
                        remaining -= len(chunk)
                        if remaining == 0:
                            break
                        chunk = reader.read(min(8 * 1024 * 1024, remaining))
                parts.append({"name": name, "bytes": part_bytes, "sha256": part_hash.hexdigest()})
                print(name, part_bytes, flush=True)
        if digest.hexdigest() != info["weight_sha256"]:
            raise SystemExit(f"Checksum mismatch for {size}; do not publish generated parts")
        manifest["models"][size] = {"file": name.split(".part")[0], "bytes": info["weight_bytes"], "sha256": digest.hexdigest(), "parts": parts}
    (args.output_dir / "weights.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("All complete model hashes verified.")


if __name__ == "__main__":
    main()
