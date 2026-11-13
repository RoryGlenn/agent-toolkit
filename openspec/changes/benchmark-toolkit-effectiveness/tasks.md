# Tasks

## 1. Build the reproducible review demo

- [x] 1.1 Add the one-file ledger, seeded refactor, clean diff, and private rollback
  probe. Verify startup in all variants and row counts of 0 for the original,
  1 for the seeded diff, and 0 for the clean diff with supported Python versions.
- [x] 1.2 Stage stock and default-bootstrap projects from the same inputs and
  document the exact `Review this diff.` prompt. Verify byte-identical product
  snapshots and diffs across arms, a clean stock profile, and a grading probe
  outside both actor projects.
- [x] 1.3 Document and exercise the demo setup, read-only review, and follow-up
  rollback check on a disposable worktree. Add tests that accept a grounded
  rollback finding and reject a fabricated finding on the clean case.

## 2. Extend the existing benchmark runner

- [x] 2.1 Add a versioned paired plan to the existing CLI and document the new
  comparison options. Verify identical user prompt hashes, reproducible order,
  frozen task/rubric/arm identities, and compatibility with historical plan reads.
- [x] 2.2 Add isolated stock, single-agent stock, and default Codex bootstrap
  staging. Verify exact installer selection and guidance hashes, normal project
  instruction discovery, authorized local Git access, and no leakage of
  comparison inputs or grading material.
- [x] 2.3 Extend native preflight and result capture for the new profile. Test
  read-only review, bounded writer access, disallowed reads and writes, a failed
  native setup, an interrupted schedule, and artifact/grade tamper rejection.
- [x] 2.4 Add generic and named worker routing to the same runner. Verify matched
  worker briefs, scopes and tools, direct worker output capture, effective
  model/effort, and observed dispatch. Test discovery-only and missing-metadata
  cases to confirm they cannot receive dispatch credit.

## 3. Build and calibrate the evaluation suite

- [x] 3.1 Define the full-toolkit case set and primary task outcomes. Include a
  normal implementation, review, consequential domain task, and a trivial task
  with overhead checks. Verify all selected oracles with correct and wrong
  controls before any actor runs.
- [x] 3.2 Give every current Codex role a declared case and negative or adjacent
  control. Verify coverage against the actual role inventory, optional
  legacy-code staging, and identical grading across stock, generic, and named
  paths. Keep missing coverage visible in the case matrix.
- [x] 3.3 Write anchored rubrics and a blind grading procedure for findings,
  documentation quality, and design judgment. Verify the grader can use the
  frozen artifact and task evidence without seeing arm identities, and that
  unresolved or unsupported claims stay out of primary success totals.
- [ ] 3.4 Create candidate held-out cases from independent project contexts.
  Record sampling units, known failure modes, accepted outputs and expected
  behaviors. Verify private probes, rubrics, and reference outputs stay outside
  actor context, and calibration cases are excluded from confirmatory counts.

## 4. Produce auditable reports

- [x] 4.1 Extend paired aggregation and document the interpretation of success,
  timeout, setup failure, unverified dispatch, review pending, and missing usage.
  Test all dispositions, correct distinct-task counts, treatment grouping,
  and equal task weighting across repetitions.
- [x] 4.2 Add deterministic paired inference for eligible campaigns and show the
  primary estimate, interval, multiplicity rule when applicable, and missing-data
  sensitivity. Test the result on a known win, tie, mixed result, and ceiling
  with inadequate sample size.
- [x] 4.3 Generate the complete public Markdown report and sanitized receipts.
  Verify claims can be reproduced from frozen data, latency and usage coverage
  are explicit, unavailable cost remains unavailable, and private or identifying
  session material is excluded by allowlist tests.

## 5. Run and publish evidence

- [ ] 5.1 Qualify one signed-in Codex CLI host and run the demo on the seeded and
  clean diffs. Retain both pairs, exact settings, each outcome, and the behavioral
  proof. Record a failed canary as a setup result and qualify another supported host.
- [ ] 5.2 Freeze and execute the proposed calibration schedule. Review quality,
  false positives, grader agreement, dispatch, time, usage, and ceiling effects.
  Retain all slots and record the resulting task and budget choices.
- [ ] 5.3 Freeze the confirmatory schedule, held-out sample, useful lift, decision
  rule, and budget. Run and blind-grade the complete campaign. Verify the final
  report preserves every planned slot and follows the frozen analysis.
- [x] 5.4 Add the demo, comparison commands, and current evidence limits to the
  README. Verify reproducibility instructions and link future full-toolkit and
  per-role results from a separate campaign.
- [ ] 5.5 Run the repository development checks and strict OpenSpec validation.
  Verify both the deterministic CI path and the qualified host path, with
  results and known limits bound to the exact toolkit revision.
