# Recovered QuillOS Deployment Note

Source: `boards/azulle-access-arm/BENCHMARKS.md` in the owner's QuillOS checkout.
The underlying repository is private; this model-specific excerpt is published
with the QuiLLM release. The note is dated May 16, 2026 and was recovered on
October 15, 2026. No underlying timing logs or repeat counts were recovered.

The note reports RK3576 NPU execution of the QuiLLM Qwen3-derived variants after
Heretic and supervised calibration. Its comparison table is transcribed here:

| Model as named in the note | Generation tokens/s | Prefill tokens/s | Peak RSS |
|---|---:|---:|---:|
| Qwen3-4B-Thinking-2507 (vanilla) | 4.40 | 47.90 | 2182.5 MB |
| QuiLLM 4B (sft8) | 4.44 | 48.58 | 2182.5 MB |

The original note describes the difference as within noise. This is deployment
evidence only, not a matched-base quality benchmark or a statistically supported
speed improvement. The recovered training base is Qwen3-4B, not the comparison
label Qwen3-4B-Thinking-2507.

The same note records that rkllm-toolkit 1.2.3 had trouble with Transformers 5.x
metadata (`layer_types`, `dtype`, `rope_parameters`, and version metadata).
That historical workaround is not an instruction to replace configurations
blindly: verify architecture and tokenizer compatibility before any NPU export.
