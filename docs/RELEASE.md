# QuiLLMv1 Research Release

Recovered Qwen3-derived local models, with the custom data, 151 completed search
trials, portable scripts, a plain-language method guide and reproducibility notes.

## Download and run

Clone the repository, then run `python3 scripts/download_weights.py --size 4b`
or use `--size 1.7b`. The downloader checks each part and the complete GGUF hash.
Follow [the reproduction guide](https://github.com/Lore-Hex/QuiLLM/blob/main/docs/REPRODUCE.md)
to import into Ollama or rebuild from a saved trial.

- 4B: 2,497,280,384 bytes, Q4_K_M, three parts.
- 1.7B: 1,257,879,360 bytes, Q5_K_M, two parts.
- `weights.json` contains all part and whole-file SHA-256 checksums.
- `LICENSE-QWEN` contains the Apache-2.0 license for the Qwen-derived weights.

Parts are ordinary byte splits, not independent models. Download all parts for
one model and use the downloader to assemble and verify them.

## Interpret the evidence carefully

The original eight political regression prompts overlap calibration data. Saved
optimizer scores are pre-calibration and pre-quantization. These are small
research checks, not an independent large-scale benchmark or a safety guarantee.
Fresh inference results and failures are documented in
[RESULTS.md](https://github.com/Lore-Hex/QuiLLM/blob/main/docs/RESULTS.md).

Full training was not repeated for this publication. Exact original weights are
provided; bit-for-bit retraining is not promised. No cloud API key is needed to
run the released model locally.
