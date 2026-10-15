# Results and How to Read Them

## Saved optimizer results, May 16, 2026

| Variant | Selected trial | Base flags | Selected flags | Questions | KL divergence |
|---|---:|---:|---:|---:|---:|
| Qwen3-1.7B-derived | 80 | 5 | 2 | 12 | 0.000875067 |
| Qwen3-4B-derived | 4 | 2 | 1 | 12 | 0.000144301 |

These values come directly from each selected trial's saved `user_attr` fields.
They describe the optimizer checkpoint **before** the later supervised
calibration and deployment quantization. Refusal/canned-answer flags are not
equivalent to incorrect answers; no broad capability score was measured here.

- [All 151 completed trials, CSV](../reports/optimizer-trials.csv)
- [Machine-readable summary and overlap counts](../reports/optimizer-summary.json)
- [1.7B raw journal](../runs/qwen3_1_7b_opi/checkpoints/models--base--Qwen3-1--7B.jsonl)
- [4B raw journal](../runs/qwen3_4b_azulle/checkpoints/models--base--Qwen3-4B.jsonl)

The journals preserve every recovered completed trial, not just the selected
ones. Some other trials score better on refusal count while changing model
behavior more. Those tradeoffs are visible in the CSV.

## Training overlap

| Probe | Questions | Exact matches in calibration |
|---|---:|---:|
| Original political probe | 8 | 8 |
| Original safety probe | 8 | 1 |
| Recovery check written October 15 | 8 | 0 |

All sets share topics with training. The third set is new wording, not evidence
of an independent domain-general benchmark. The counts are reproduced by
`python3 scripts/summarize.py`; they are not hand-entered estimates.

## Deployment evidence

An archived QuillOS RK3576 NPU note reported these values on May 16:

| Model named in the note | Generation tokens/s | Prefill tokens/s | Peak RSS |
|---|---:|---:|---:|
| Qwen3-4B-Thinking-2507 | 4.40 | 47.90 | 2182.5 MB |
| QuiLLM 4B sft8 | 4.44 | 48.58 | 2182.5 MB |

This is a historical engineering note, not a fresh controlled performance
benchmark. The comparison model is named differently from the recovered
training base, so it must not be used to infer a matched-base quality comparison.
The small speed difference does not support a speed-improvement claim.
[Original QuillOS note](https://github.com/Lore-Hex/quillos/blob/main/boards/azulle-access-arm/BENCHMARKS.md).

## Reproduce the numbers

`python3 scripts/summarize.py --check` recomputes the historical summary from the
raw journals and verifies that the published report matches. Runtime checks use
the published script, prompts and Modelfiles. Read [limitations](LIMITATIONS.md)
before interpreting percentages.
