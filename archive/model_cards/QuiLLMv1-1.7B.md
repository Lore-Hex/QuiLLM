# QuiLLMv1-1.7B Model Card Draft

## Base

`Qwen/Qwen3-1.7B`

Qwen3.6 is the preferred family direction, but Qwen3.6 does not currently publish an official 1.7B open checkpoint. If a Qwen3.6 1.7B checkpoint is released, this card should be updated and the run reproduced.

## Intended Use

QuiLLMv1-1.7B is a local QuillOS assistant for small devices. It should answer ordinary system, troubleshooting, writing, and factual questions. It should answer lawful political and historical questions neutrally, including China-sensitive topics.

## Debiasing Scope

The Heretic prompt split targets China-state political censorship and canned CCP-aligned responses on topics such as Tiananmen, Taiwan, Xinjiang, Falun Gong, the Great Firewall, Hong Kong, and political dissidents.

The build is not intended to remove safety behavior for harmful requests. Safety preservation is part of the release gate.

## Required Eval Results

Fill these in after a real run:

- Heretic selected trial:
- KL divergence:
- Censorship-refusal count:
- Political probe pass rate:
- Safety probe pass rate:
- Manual review notes:

## Known Limitations

- Abliteration can reduce refusals without guaranteeing factuality.
- Canned-answer markers are heuristic and can miss subtle propaganda framing.
- Small models may hallucinate even after censorship behavior improves.
- GGUF `Q5_K_M` is the current minimum release quantization. `Q3_K_M` and `Q4_K_M` are experimental-only for this 1.7B candidate because they did not preserve the political probe reliably enough.
