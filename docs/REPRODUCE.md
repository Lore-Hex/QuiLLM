# Reproduce QuiLLM with Your Agent

There are three levels. Start with the first. Running an existing model is much
cheaper than retraining it, and inspecting the evidence costs no model calls.

## Check the evidence

Install Git and Python 3.12 or newer, then:

```bash
git clone https://github.com/Lore-Hex/QuiLLM.git
cd QuiLLM
python3 scripts/summarize.py --check
python3 -m unittest discover -s tests -v
```

This reads the saved journals, checks the report, and tests the utilities.
It needs no GPU, API key, paid service, or training environment.

## Run the existing model

Install [Ollama](https://ollama.com/download), start it, and run:

```bash
python3 scripts/download_weights.py --size 4b
ollama create quillm-research:4b -f modelfiles/QuiLLMv1-4B.Modelfile
ollama run quillm-research:4b
```

Use `--size 1.7b` and `modelfiles/QuiLLMv1-1.7B.Modelfile` for the smaller model.
Give it its own tag, such as `quillm-research:1.7b`.
The downloader verifies every release part and the reassembled file before
installing it. The 4B download is 2.50 GB; 1.7B is 1.26 GB. Runtime memory is
higher than file size. Ask your agent to check free RAM and disk space first.

Test both kinds of behavior and read the output:

```bash
python3 scripts/evaluate_ollama.py --model quillm-research:4b --probe evals/political_probe.jsonl --report private/politics.json
python3 scripts/evaluate_ollama.py --model quillm-research:4b --probe evals/safety_preserve_probe.jsonl --report private/safety.json
python3 scripts/evaluate_ollama.py --model quillm-research:4b --probe evals/recovery_probe_20261015.jsonl --report private/recovery.json
```

An exit code of 1 means at least one check failed. Keep that result. Do not edit
questions or scoring just to get a green result. Raw reports are local and may
contain unsafe responses; review before publishing. They are ignored by Git.

## Rebuild from the saved trial

This does real model work. Your agent should inspect hardware, available memory,
disk and expected runtime with you before proceeding. CPU-only training can be
slow. The historical script used Apple MPS or CPU; the portable script also
recognizes NVIDIA CUDA. We have not rerun full training for this public release.

Create a separate Python 3.12 environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[train]'
```

These versions match recovered package metadata. Do not upgrade Heretic without
checking its configuration and export APIs. Install build tools including CMake
and a C/C++ compiler, then build the recorded llama.cpp revision:

```bash
git clone https://github.com/ggml-org/llama.cpp tools/llama.cpp
git -C tools/llama.cpp checkout 64b38b561b987679c4e1c6231f93860d3eec2638
python -m pip install -r tools/llama.cpp/requirements/requirements-convert_hf_to_gguf.txt
cmake -S tools/llama.cpp -B tools/llama.cpp/build
cmake --build tools/llama.cpp/build --target llama-quantize -j 4
bash scripts/rebuild.sh 4b
```

Use `1.7b` for the other model. The helper downloads the recorded Qwen base
revision, reapplies the selected saved Heretic trial, runs the calibration, merges
the adapter, converts to GGUF and quantizes. Existing output paths are protected.
Run the Ollama import and evaluations above afterwards.

**This is a reproducible recipe, not a promise of identical new file hashes.**
The release checksums identify the recovered original weights. New hardware,
library builds and floating-point behavior may produce different hashes.

## Repeat the entire search

The saved-trial path avoids the original 100/51 completed search trials. If you
want to study the optimizer itself, use a fresh checkout and obtain compute
approval before starting:

```bash
HERETIC_STUDY_CHECKPOINT_DIR=outputs/new-search-4b bash scripts/run_heretic.sh --config configs/quillmv1-qwen3_4b-azulle.toml --model models/base/Qwen3-4B
```

First download the pinned base as above. The command uses a **new** checkpoint
directory; choose a new path if it already exists. This keeps the historical
journals untouched. The original
config budgets are 160 trials for 4B and 220 for 1.7B, not the number actually
completed. Heretic's final selection is interactive. You can instead export a
chosen completed trial with `scripts/export_heretic_trial.py`.

The archived configuration files alone do not reproduce every run setting:
the **settings saved inside the journal** are authoritative for saved-trial
reconstruction. For example, the recovered 4B run has a response prefix and
resolved batch size in that journal.
