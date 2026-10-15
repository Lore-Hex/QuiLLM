#!/usr/bin/env python3
"""Download and verify the public GGUF release without third-party packages."""
import argparse
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://github.com/Lore-Hex/QuiLLM/releases/download/v1.0.0"


def assemble(info, destination, open_part):
    """Verify each part and the complete model before atomically installing it."""
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Already exists: {destination}; verify it or choose a new location")
    destination.parent.mkdir(parents=True, exist_ok=True)
    total_hash = hashlib.sha256()
    total_bytes = 0
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        partial = Path(temporary) / "model.partial"
        with partial.open("wb") as writer:
            for part in info["parts"]:
                if Path(part["name"]).name != part["name"]:
                    raise ValueError("Invalid part filename")
                digest = hashlib.sha256()
                count = 0
                with open_part(part["name"]) as reader:
                    while chunk := reader.read(8 * 1024 * 1024):
                        count += len(chunk)
                        if count > part["bytes"]:
                            raise ValueError("Part exceeds expected size")
                        writer.write(chunk)
                        digest.update(chunk)
                        total_hash.update(chunk)
                if count != part["bytes"] or digest.hexdigest() != part["sha256"]:
                    raise ValueError(f"Invalid download: {part['name']}")
                total_bytes += count
                print(f"Verified {part['name']}", flush=True)
        if total_bytes != info["bytes"] or total_hash.hexdigest() != info["sha256"]:
            raise ValueError("Complete-model checksum mismatch")
        # A hard link fails if a concurrent download has already installed the target.
        destination.hardlink_to(partial)
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=["1.7b", "4b"], default="4b")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    info = json.loads((ROOT / "models/weights.json").read_text())["models"][args.size]
    if Path(info["file"]).name != info["file"]:
        raise SystemExit("Invalid model filename")
    result = assemble(info, args.output_dir / info["file"],
                      lambda name: urllib.request.urlopen(BASE_URL + "/" + name, timeout=120))
    print(f"Verified complete model: {result}")


if __name__ == "__main__":
    main()
