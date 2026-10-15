# Sources, Licensing and Recovery

This release was recovered from the owner's archived QuiLLM project and locally
installed Ollama weights. It does not include cloud API secrets, account data,
private conversations, the original private Git history, or virtual environments.

## Upstream work

- [Qwen3](https://github.com/QwenLM/Qwen3), including
  [Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B) and
  [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B): Apache-2.0 model licenses.
- [Heretic](https://github.com/p-e-w/heretic): AGPL-3.0-or-later. The recovered
  environment used `heretic-llm==1.3.0`. It provides the weight-editing/search
  implementation. QuiLLM's contribution is the targeted data, configuration,
  calibration, packaging and documented experiment, not invention of abliteration.
- [llama.cpp](https://github.com/ggml-org/llama.cpp): MIT; conversion and GGUF quantization.
- [PEFT](https://github.com/huggingface/peft) and
  [Transformers](https://github.com/huggingface/transformers): Apache-2.0.
- [Ollama](https://github.com/ollama/ollama): MIT; local model serving.
- [AUGMXNT's deccp research](https://github.com/AUGMXNT/deccp) was cited by the
  original project as related work. This repository publishes the recovered
  custom prompts, not a bulk copy of that external dataset.

The repository's code and custom prompt files use AGPL-3.0-or-later. This does
not relicense upstream packages, Qwen weights/tokenizers, or third-party research.
The released weights are modified Qwen3 model files and retain Apache-2.0 terms;
the original base creators should be credited when redistributing them.

## Evidence and publication changes

The original project commit is recorded in [provenance](../models/provenance.json).
It identifies an archived private checkout; it is not presented as a publicly
resolvable upstream commit. The public repository starts with a clean history.

Original script copies are in `archive/scripts/`. The main scripts add:

- empty-answer and invalid-probe rejection;
- persistent local JSON evaluation reports;
- CUDA selection in addition to the historical MPS/CPU path;
- rejection of fully truncated training labels and accidental output overwrites;
- saved calibration settings/losses for future runs;
- checksum-verified weights, a report calculator, and a documented rebuild helper.

The historical training/model-card draft is retained under `archive/model_cards/`
and remains a draft. Recovered metadata in `archive/output-metadata/` is not a
complete Hugging Face model directory. Large shards/tokenizers must be downloaded
or rebuilt as documented. No optimizer scores were rewritten to improve results.
