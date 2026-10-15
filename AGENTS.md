# Instructions for an agent helping a person reproduce QuiLLM

Read README.md, docs/REPRODUCE.md, docs/METHOD.md and docs/LIMITATIONS.md first.
Explain the plan in ordinary language. Offer these levels in this order:

1. Inspect the published data and recompute the report. No GPU or API key.
2. Run the released model locally and inspect its answers with the user.
3. Rebuild from the saved Heretic trial and calibration data.
4. Repeat the full search only with explicit compute/time approval.

Use a fresh environment. Never overwrite an existing model tag or training output.
Run `python3 -m unittest discover -s tests -v` and
`python3 scripts/summarize.py --check` before changing or training anything.
The selected trials use Heretic's one-based `index`: 80 for 1.7B and 4 for 4B.
Use the recorded base-model revisions and historical dependency versions.
Do not silently substitute current Heretic: its API/configuration can change.

This experiment targets refusals on lawful political/historical questions.
Preserve the safety calibration and safety probes. Never optimize for compliance
with harmful requests. Passing these small probes does not establish general safety.

Distinguish optimizer results, training-overlap regression probes, fresh checks,
and independent benchmarks. The repository contains no broad independent benchmark.
New results must record model/weight hashes, runtime version, prompts, parameters,
date, errors, sample counts, and the exact scoring method. Do not edit a test after
seeing its output and continue to call it held out.

Do not publish credentials, private paths, account identifiers, user conversations,
or harmful operational output from failed safety tests. Store failed safety output
privately for review; public reports may include its hash and failure classification.
Keep originals in archive/scripts unchanged. Document any portability fixes.
