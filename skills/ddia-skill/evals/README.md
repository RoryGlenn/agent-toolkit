# DDIA capability evaluation

The public case catalog contains fourteen chapter-spanning tasks and three controls:
harmless repetition, a cosmetic change and an already-correct capacity transaction.
These are authored constructed tasks, not held-out cases or measured agent results.
They exercise combinations of concepts; a chapter-level score does not prove mastery of
every linked concept. Add curator-held-out tasks before making broader effectiveness claims.

Use the shared skill's helpers from any directory:

```bash
python3 /resolved/ddia-skill/scripts/guide.py check
python3 /resolved/ddia-skill/scripts/guide.py check --source-index /explicit/library/index.json
python3 /resolved/ddia-skill/scripts/experiments.py all
python3 /resolved/ddia-skill/evals/evaluate.py list
```

Eight bounded experiments include broken and sufficient controls. Admission/replay use
actual SQLite transactions; remaining experiments are small deterministic models or JSON
round-trips. They demonstrate their named invariant and oracle sensitivity, not behavior
of a live broker, PostgreSQL isolation, provider, failover service or production recovery.
No bundled experiment proves agent effectiveness. Schema examples do not execute Avro or
Protocol Buffers. Publication models do not establish filesystem power-loss durability.

## Controlled comparison

Choose an explicit saved **current** shared skill, such as the pre-redesign version from
Git. The redesigned skill defaults to the helper's installed package. Freeze all inputs
before execution; keep the same model, effort and declared tool/time budget in all arms.

```bash
python3 /resolved/ddia-skill/evals/evaluate.py plan \
  --current-skill /explicit/pre-redesign/ddia-skill \
  --output /new/comparison-directory --trials 3 --seed 17 \
  --model MODEL --effort high --budget 'same declared time/tool budget'
```

The planner snapshots identical tasks for **baseline**, **current**, and **redesigned**
arms, shuffles arm order per repetition, and fingerprints actor files and the grader plan.
By default original source is withheld from both specialist arms. To compare source-backed
conditions, supply `--source-library /explicit/library` containing a matching source.epub
and index.json; the same source is copied to both specialists and fingerprints are recorded.
Baseline intentionally has no DDIA resources. This measures the package/resource condition,
not a pure prompt-only difference. Never silently use ambient personal source libraries.

Each `actors/RUN/` contains only its task and guidance resources. Grading criteria and other
case prompts are withheld from actor snapshots. Run each in a fresh isolated session with
only that directory and permitted tools exposed. Store responses and tool evidence outside
the actor directory so its frozen inputs remain unchanged. Do not show earlier answers or
reviewer conclusions to later actors. Record actual model/settings, elapsed time, token/tool
cost and deviations in the experiment narrative.

**The planner does not launch models or enforce sandboxing, fresh context, budgets, settings
or blinding.** The host/experiment operator must provide those boundaries. Hashes detect
accidental changes; they are not a hostile-actor security seal. The tasks and rubrics are
public, so this is not a private held-out benchmark. A previously exposed actor is not a
valid independent sample of these tasks.

## Independent semantic grading

Give a reviewer the frozen case criteria and response plus observable tool artifacts,
without the arm label or author justification where practical. Full blinding is unlikely
because source references can reveal the condition. Do not use the writer as its own
independent grader. Score each criterion 0 absent/incorrect, 1 partial, 2 clear/correct.
Use semantic evidence, never keyword, line-count or citation-count proxies.

Review must consider missed consequential failures, false-positive blockers, invented
assumptions, unnecessary infrastructure, verification scope and operational cost. Correct
controls matter as much as broken cases. Separate executed checks from proposed tests.
Book traceability is useful provenance but does not add correctness points by itself.

A score file contains each frozen criterion exactly once:

```json
{
  "c1": {"score": 2, "evidence": "Observed recommendation and supporting response/tool evidence"},
  "c2": {"score": 1, "evidence": "Specific partial coverage and missing consequence"},
  "c3": {"score": 2, "evidence": "Specific observed behavior"},
  "c4": {"score": 0, "evidence": "Specific omission or incorrect claim"}
}
```

```bash
python3 /resolved/ddia-skill/evals/evaluate.py record /comparison-directory \
  --run RUN --response /response.txt --scores /scores.json --reviewer independent-reviewer
python3 /resolved/ddia-skill/evals/evaluate.py report /comparison-directory
```

Recording refuses duplicate receipts. Verify/report detect changes to frozen actor inputs.
Reports disclose missing observations, per-arm mean/sample variation and matched differences.
They do not infer statistical significance or declare superiority. Preserve failures and
all planned observations; do not selectively report successful cases.

The earlier local four-task comparison tied baseline and specialist at 32/32. It established
source traceability, not better correctness. Preserve that result rather than treating this
expanded corpus or fixture success as evidence of improvement. New measured trials belong
in separately versioned evidence with exact input fingerprints, methods and limits.

## Issue 8 forward reasoning pilot

The [preserved one-trial pilot](pilots/issue-8/README.md) scored baseline 40/40,
pre-redesign specialist 39/40, and redesigned specialist 40/40. It found a narrow completeness
omission in the pre-redesign response and no demonstrated improvement over baseline. Raw
requests, rubric, responses, source/snapshot fingerprints and independent scoring are included.
This four-scenario bundled-response pilot is separate from the seventeen public suite cases;
its partial blinding and unenforced tool/isolation controls limit the result.
