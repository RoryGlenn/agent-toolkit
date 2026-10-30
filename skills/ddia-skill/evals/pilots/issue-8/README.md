# Issue 8 forward reasoning pilot

This pilot found **no demonstrated improvement over the baseline**. Each arm produced one
response covering the same four bundled scenarios. An independent reviewer scored the frozen
20-criterion rubric, with two points available per criterion. Source citations did not earn
correctness points.

| Arm | Reviewer label | Score |
| --- | --- | ---: |
| Ordinary agent without DDIA guidance | Cedar | 40/40 |
| Pre-redesign DDIA specialist | Maple | 39/40 |
| Redesigned DDIA specialist | Birch | 40/40 |

The one-point difference was a completeness omission in the pre-redesign response: it did
not explicitly distinguish deleting training examples from removing their influence in an
already trained model. The reviewer found no material incorrect systems-design claim in any
response. These near-ceiling content scores demonstrate the observed reasoning coverage,
not correct execution, a general winner, or production superiority.

## Frozen evidence and provenance

- [Requests](requests.txt) and [rubric](rubric.json) were frozen before responses.
- Raw responses are preserved as [baseline](baseline.md), [current](current.md), and
  [redesigned](redesigned.md).
- [Independent scores](independent-scores.json) preserve per-criterion evidence and rationale;
  [independent comparison](independent-comparison.md) preserves the reviewer's interpretation.
- The original [manifest](manifest.json) records arm labels, totals, source fingerprints and
  SHA-256 hashes for all seven other imported artifacts. All eight files were imported
  verbatim; the duplicated blinded-response folder is not included.

The current arm used base commit
[`9d89ddc21b3955cf71320f81dfaa99c8d3d39ed8`](https://github.com/RoryGlenn/agent-toolkit/commit/9d89ddc21b3955cf71320f81dfaa99c8d3d39ed8).
The redesigned arm used the initial implementation tree
`5c871972fde608a5ed26239fe7c0090dbc962e19`. The later product-code correction closes SQLite
setup/readback connections in the admission experiment and adds its regression test. This
pilot was not rerun after that correction; this evidence import is a subsequent documentation
change. These results are separate from the seventeen public evaluation-suite cases and do
not change the coverage ledger's per-concept `not-measured` states.

## Interpretation limits

There was one trial per arm, with four scenarios bundled into one response rather than four
independent observations. Cases and rubric were author-created. All arms inherited the same
model/reasoning settings and received the same response word limit; tool budgets and host
isolation were instructions, not enforced experimental controls. Independent review used
arbitrary labels without the arm mapping, but citations could reveal source access, so
blinding was partial. The reviewer did not verify source locators or actual retrieval use.

This was a reasoning-only pilot. It exercised no live engine, broker, billing outcome, load,
failover or disaster recovery, and supplies no production correctness, statistical significance,
repeatability or superiority claim. Preserve all responses and the narrow omission alongside
the scores; do not treat expanded reference coverage or fixture success as measured agent
improvement.
