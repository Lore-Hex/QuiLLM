# What This Release Does and Does Not Establish

- **The original political probe overlaps training.** All 8 prompts appear
  verbatim in the 30-example calibration data. The safety probe has 1 exact
  match out of 8, plus substantial topic overlap. These are regression checks.
- **The 12 optimizer questions are tuning data.** Many trials were evaluated
  against them. Selected-trial improvements are not independent test results.
- **The new recovery probe is still small and topic-adjacent.** It was written
  before the release-time run, but mostly examines similar subjects. It is not a
  substitute for a large independent, multilingual, human-reviewed evaluation.
- **Keyword scoring is crude.** It can penalize a quoted slogan in a neutral
  answer, miss a misleading answer, or count a refusal followed by unsafe help.
  The public report includes political text for inspection, not just percentages.
- **Safety is an intention, not a certified property.** Weight edits and small
  fine-tunes can weaken safeguards. The published suite cannot measure all harms.
- **No general capability claim.** There are no recovered MMLU, coding, math,
  independent bias, or comprehensive factuality benchmark results for this model.
- **Not bit-for-bit retraining.** Base config revisions, package versions, saved
  trials, templates and data were recovered. Original SFT command/loss logs and
  complete hardware/environment determinism records were not. Floating-point
  and backend differences can change newly rebuilt weights and answers.
- **Runtime matters.** The archived BeeLink deployment used a shorter template
  and different sampling settings than the canonical published Modelfile. Its
  installed behavior is not interchangeable with the release-time Ollama test.
- **Model names can be misleading.** On the recovery machine, `qwen3-4b` was an
  alias for QuiLLM weights. It was not used as a vanilla baseline. Model hashes,
  not names, establish which file was tested.
- **Dates describe different things.** Optimizer journals record May 16, 2026.
  Recovery and fresh inference checks are dated October 15, 2026. Fresh results
  must not be described as the original historical evaluation.
- **No measured historical training cost.** We did not recover a reliable cost
  or duration ledger. Do not infer training cost from the tiny dataset size.

For a stronger evaluation, freeze new disjoint prompts and scoring rules, run
the actual unmodified base and the final model under identical settings, blind
the human graders, include varied languages and normal tasks, and report failures
and uncertainty alongside improvements.
