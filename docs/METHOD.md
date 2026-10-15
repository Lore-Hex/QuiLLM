# How QuiLLM Was Made

## The idea

An assistant should be able to explain a historical event, including politically
sensitive events. It should also decline to help someone commit violence or
steal another person's information. Those are different behaviors. The experiment
tries to change the first without losing the second.

"Abliteration" here means editing weights along an estimated internal direction.
It is not deleting facts, installing a system prompt alone, or making a universal
truth detector. This project uses a targeted version of that technique.

## 1. Start with a small existing model

The actual archived bases are `Qwen/Qwen3-1.7B` and `Qwen/Qwen3-4B`.
The larger Qwen3.6 configuration files are historical experiment plans, not
evidence that those models were trained or released.

Both base-model config download revisions are recorded in
[provenance.json](../models/provenance.json). These came from the saved Hugging
Face download metadata, not an invented version number. The full original base
shards are not duplicated in Git; the rebuild downloads them from Qwen.

## 2. Build two comparison sets

The 40 "bad prompts" are **lawful questions**, not requests for harm. "Bad" is
Heretic's historical configuration label for the behavior to change. Topics
include Tiananmen, Taiwan, Xinjiang, Hong Kong, censorship and political dissent.

The 40 "good prompts" ask comparable historical and political questions about
other countries. Heretic compares their mean internal activations with those
from the targeted set. The difference is normalized, with an optional projection
removed to reduce overlap with the comparison direction.

See [target questions](../datasets/ccp_censorship_prompts/train.jsonl) and
[comparison questions](../datasets/refusal_direction_good/train.jsonl).

## 3. Search for a limited weight edit

Heretic 1.3.0 searches over the direction and how strongly it edits output
projections in attention and feed-forward layers. The saved journals contain the
actual parameters, scores, seed, settings and completed-trial records.

It tries to reduce refusal/canned-answer markers on 12 political prompts and
limit KL divergence on 18 preservation prompts. The latter include ordinary
help and harmful requests where the original refusal behavior should remain.
This is a statistical constraint, not a guarantee that harmful behavior cannot
change. Run the safety tests and inspect answers after every stage.

The selected trial indices are **80 for 1.7B** and **4 for 4B**. They are the
one-based `user_attr.index` values in the journals, not zero-based Optuna IDs.
There were 100 and 51 completed trials, respectively. The larger configured
budgets of 220 and 160 must not be reported as completed work.

## 4. Calibrate with short supervised examples

[The complete calibration set](../datasets/calibration/quillmv1_sft.jsonl)
contains 30 prompt-answer pairs. They correct specific factual/framing failures
and reinforce refusals for harmful requests. This is why the release is more
than the initial weight edit.

The archived script uses LoRA rank 8, alpha 16, dropout 0.05, and the projection
modules `q_proj`, `v_proj`, `o_proj`, `down_proj`. It trains answer tokens only,
with AdamW, learning rate 0.0002, batch size 1, maximum sequence length 1024 and
seed 16064. It then merges the adapter back into the model. Artifact names record
4 epochs for 1.7B and 8 for 4B; a historical loss curve was not recovered.

## 5. Compress and run locally

llama.cpp converts the model into GGUF. The selected formats are Q5_K_M for
1.7B and Q4_K_M for 4B. Smaller files use less memory but may change behavior;
the archived notes rejected smaller 1.7B quantizations after probe failures.

Ollama loads the GGUF with a published template, system message, and sampling
settings. Those settings are part of the experiment. A different template or
system message can produce different answers with identical weights.

## 6. Read the results honestly

We publish the training/test overlap, unsuccessful trials, the heuristic scoring
code, and the observed failures. A low refusal rate alone says little about
truthfulness. A safe-looking sentence followed by harmful detail must not be
counted as safe merely because it includes "I cannot".

See [results](RESULTS.md), [limitations](LIMITATIONS.md), and
[the exact reproduction procedure](REPRODUCE.md).
