# Pinned FreedomBench sources

Copied without modification from [Lore-Hex/FreedomBench](https://github.com/Lore-Hex/FreedomBench)
commit `cc037ac7b286ba4f910309162367d856cbd25d58` (package 1.0.2).
The vendored files retain their Apache-2.0 license in `vendor/LICENSE`.

`questions.py` supplies all 60 questions, sources and deterministic option ordering.
`classify.py` supplies the original answer extractor and scorer. `run.py` supplies
the exact quiz system message and prompt builder. The local runner loads just
those two definitions from its syntax tree, avoiding an unused API SDK dependency.
Source hashes are recorded in every result file.

The transport is local Ollama, not TrustedRouter. Both models receive identical
raw Qwen ChatML prompts with an empty, closed thinking block (non-thinking mode).
The benchmark's 8192-token maximum and up-to-four retries for answers without a
parseable letter are preserved. Every attempt is saved, including truncated
output; wrong-but-parseable answers are never retried. Infrastructure failures
remain errors rather than being described as model refusals.

This is a same-owner benchmark, not an independent third-party evaluation.
Its subjects overlap QuiLLM's political calibration data. A high score on these
multiple-choice questions does not establish open-ended factuality or safety.
