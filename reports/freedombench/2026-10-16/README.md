# FreedomBench local comparison: October 16, 2026

Generated from all 240 Beelink answers using the unchanged FreedomBench scorer.

| Model | Quantization | Correct / 60 | Score | Incorrect choice | No parsed choice | Errors |
|---|---|---:|---:|---:|---:|---:|
| [Qwen3 1.7B (unmodified)](qwen3-1.7b.json) | Q5_K_M | 53 / 60 | 88.33% | 7 | 0 | 0 |
| [QuiLLMv1 1.7B](quillm-1.7b.json) | Q5_K_M | 49 / 60 | 81.67% | 11 | 0 | 0 |
| [Qwen3 4B (unmodified)](qwen3-4b.json) | Q4_K_M | 57 / 60 | 95.00% | 3 | 0 | 0 |
| [QuiLLMv1 4B](quillm-4b.json) | Q4_K_M | 50 / 60 | 83.33% | 4 | 6 | 0 |

The upstream scorer calls answers without a parsed A-D choice `refused`.
That includes prose and formatting failures, not only actual refusals.
These are benchmark scores, not general factuality or safety scores.

## Paired changes

| Size | QuiLLM minus Qwen | Newly correct | Newly missed | Both correct | Both missed |
|---|---:|---:|---:|---:|---:|
| 1.7B | -6.67 percentage points | 2 | 6 | 47 | 5 |
| 4B | -11.67 percentage points | 1 | 8 | 49 | 2 |

## Topic scores

| Topic | Qwen 1.7B | QuiLLM 1.7B | Qwen 4B | QuiLLM 4B |
|---|---:|---:|---:|---:|
| censorship | 4 / 5 | 3 / 5 | 4 / 5 | 3 / 5 |
| covid | 5 / 5 | 5 / 5 | 5 / 5 | 4 / 5 |
| dissidents | 5 / 5 | 4 / 5 | 5 / 5 | 5 / 5 |
| falun_gong | 4 / 5 | 5 / 5 | 4 / 5 | 3 / 5 |
| hong_kong | 5 / 5 | 5 / 5 | 5 / 5 | 5 / 5 |
| mao_era | 4 / 5 | 4 / 5 | 5 / 5 | 4 / 5 |
| taiwan | 3 / 5 | 2 / 5 | 5 / 5 | 3 / 5 |
| territory | 4 / 5 | 4 / 5 | 5 / 5 | 5 / 5 |
| tiananmen | 5 / 5 | 4 / 5 | 5 / 5 | 4 / 5 |
| tibet | 5 / 5 | 4 / 5 | 5 / 5 | 4 / 5 |
| xi_ccp | 5 / 5 | 5 / 5 | 5 / 5 | 5 / 5 |
| xinjiang | 4 / 5 | 4 / 5 | 4 / 5 | 5 / 5 |

## Execution

| Model | Requests including retries | Output tokens | Truncated attempts |
|---|---:|---:|---:|
| Qwen3 1.7B (unmodified) | 60 | 324 | 0 |
| QuiLLMv1 1.7B | 60 | 139 | 0 |
| Qwen3 4B (unmodified) | 60 | 5165 | 0 |
| QuiLLMv1 4B | 84 | 4241 | 0 |

All inference ran locally, with no paid inference API or judge calls.
Electricity and existing hardware costs are not measured.

[Methodology, interpretation and reproduction](../../../docs/FREEDOMBENCH.md)
