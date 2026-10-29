Implement https://github.com/RoryGlenn/agent-toolkit/issues/5 using the
`codex/large-project-cloud-handoff` branch as the starting point. Read the full issue,
repository `AGENTS.md`, `README.md` development checks, `benchmarks/README.md`, and
`benchmarks/large_projects/README.md` before implementation.

The four-case curation handoff is committed here. Existing macOS qualification summaries
are historical evidence, not Linux/cloud proof. Source pins, test-patch digests, task drafts,
commands and limitations are under `benchmarks/large_projects/`. Original local caches and
logs are neither required nor accessible. Prepare fresh curator workspaces with `prepare.py`
as needed, then integrate the accepted work into the existing benchmark mechanisms.

Complete issue #5: portable case preparation and adapters, fair behavioral grading,
verified candidate/evaluator isolation, bounded execution and cleanup, reproducible evidence,
and fresh-environment qualification of all four cases. Do not expose this handoff, fixed Git
objects, hidden tests, solution links or compiled curator caches to candidate agents.
Do not run a baseline-versus-toolkit comparison or claim specialist superiority.

Use one implementation writer. Preserve unrelated work. After a stable diff, obtain an
independent read-only review and independent verification following the repository's
issue-to-tested-PR workflow. If independent agents are unavailable, report that limitation;
self-review does not satisfy independent verification. Serialize heavy builds initially,
limit compiler parallelism to two, and monitor disk/memory. Run exact repository gates and
case-specific checks, report failures/skips honestly, and test timeout/cleanup paths.

Check the actual cloud network policy, available toolchains and privileges first. Download
only necessary source/dependencies with permitted access. Never weaken isolation to make a
canary pass. If a required boundary cannot be enforced, complete useful preparation and
report the precise blocker instead of marking the case ready.

Commit and push the completed work to the working branch and open/update a review-ready PR
linked to issue #5. Do not merge, run a comparison study, contact upstream maintainers or
provision paid infrastructure without separate authorization. State what remains unverified.
