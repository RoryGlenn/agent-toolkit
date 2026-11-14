# Final source-bound verification

Verified 2026-10-31. This pass binds feature scores to a separate fixed original source snapshot and verifies the integrated runtime sources. It is final source-bound validation, not a model retry: no actor/model/API call was launched, no candidate/evaluator/product code was edited by the verifier, and all initial evidence remains preserved. No final grade was overwritten and no diagnostic rerun was needed.

## Fixed original source proof

- Reference path for every final command: `/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original`.
- Original commit: `0b36e7d4e95300b16a713edf831c8613dba46b69`.
- Original tree: `173fc826479ad7859d34d106a525b62ba1725a58`.
- Manifest: `work/pilot-original-manifest.json`; SHA-256 `569613b0f7badb1980e171077fd6bc27715b3ea83893d9889f3b18d616f633fd`.
- Independent proof passed: manifest paths/modes/blob SHAs exactly matched `git ls-tree` for the original commit; its tree ID matched `git rev-parse`; all 195 snapshot entries matched their recorded Git blob SHA and Git mode, with no extra or missing entries. Each blob was hashed as SHA-1 of `blob <byte-length>\0<bytes>` without writing Git objects. Complete per-path results are in `final/fixed-source-proof.json`.
- This fixed reference avoids relying on the original working checkout after integration began. The final evidence below is the authoritative source-bound validation; initial scoring evidence and the original scored evaluator are retained as historical records.

Exact Git source-proof commands:

```sh
git -C /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit ls-tree -r -z 0b36e7d4e95300b16a713edf831c8613dba46b69
git -C /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit rev-parse '0b36e7d4e95300b16a713edf831c8613dba46b69^{tree}'
```

## Packaged evaluator semantic review

- Packaged evaluator: `work/agent-toolkit/experiments/openspec-pilot/evaluate.py`; SHA-256 `7006189575f84477b17452308a25debfba2d6daa5ea10a3668890018015781c7`.
- Preserved originally scored evaluator: `work/agent-toolkit/experiments/openspec-pilot/evidence/initial/scored-evaluator.py.txt`; SHA-256 `eedafb2fd16561258b2631b952cc34b24179b9b5e2848f0b8f69cf5b4e50752b`.
- The full diff was independently reviewed. All 30 assertion ASTs are identical. Other changes are formatting, moving `Callable` to `collections.abc`, adding `typing.cast` around parsed manifest data without runtime conversion, and replacing bound-default lambdas with equivalent `functools.partial` bindings. Catalog `expected` and `human` values are not rebound after registration. Probe modes, mutations, CLI commands, snapshots and exit rules are unchanged. Machine-readable review is in `final/evaluator-semantic-review.json`.
- First-inspection and subsequent applicable read-only checks retain the corrected inode/mode/mtime/content/link-target snapshots. Positive feature controls are still mandatory before rejection assertions, so unsupported commands cannot earn rejection credit.

## Results

| Contract | Frozen a | Frozen b | Fixed original negative control | Integrated source |
| --- | ---: | ---: | ---: | ---: |
| catalog-json | 7/7 | 7/7 | 0/7 | 7/7 |
| project-check | 16/16 | 16/16 | 0/16 | 16/16 |
| personal-status | 12/12 | 12/12 | 0/12 | 12/12 |

All nine positive candidate/integrated evaluator processes exited 0 and every probe passed. All three fixed-original processes exited 1 and every probe failed at its unsupported feature positive control, as expected. No process error, timeout, candidate failed probe, malformed grade artifact, or diagnostic rerun occurred. Final frozen-candidate scores match the initial scores.

Independent raw-output review is retained in `final/stdout-state-review.json`. For every frozen slot and integrated source, it confirmed exact personal-status destination names and states for all 12 modes, expected exit codes, schema version, all 15 Copilot skill-only entries, dependency closure and deduplicated role. It also confirmed project diagnostics identify the perturbed file/block/manifest or conflicting option, while intact/unowned/source-only-change modes succeed. Catalog outputs contained 15 skills and passed the unchanged full-inventory, dynamic-source, deterministic and human-compatibility assertions.

Input integrity checks passed before and after the final pass:

- Evaluator SHA-256 was stable.
- All six frozen directory hashes were stable and matched the initial verification fingerprints.
- The fixed original snapshot directory hash was stable.
- Integrated runtime product fingerprints (`install.py`, `project_bootstrap.py`, `skills/`, `agents/`) were stable. Reports/evidence were excluded from this integrated product fingerprint because the controller was updating reports during the pass. Exact component fingerprints and process-level receipts are in `final/verification-run-receipts.json`.

## Exact final evaluator commands

Every command ran from `/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4` with the locked development interpreter and a maximum of three independent evaluator subprocesses at once. Outputs below are new artifacts under `evidence/final/`; all initial grade artifacts remain in place. Per-probe command argv, stdout, stderr and exits are retained in each final grade JSON. No `HOME`/`CODEX_HOME` override or global environment/configuration change was made.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py catalog-json /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/catalog-json/a --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/catalog-json-a-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "catalog-json", "passed": 7, "total": 7}`; stderr `(empty)`; elapsed 2.2311 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py catalog-json /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/catalog-json/b --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/catalog-json-b-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "catalog-json", "passed": 7, "total": 7}`; stderr `(empty)`; elapsed 2.1958 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py catalog-json /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/catalog-json-integrated-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "catalog-json", "passed": 7, "total": 7}`; stderr `(empty)`; elapsed 2.6585 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py catalog-json /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/catalog-json-original-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 1; stdout `{"case": "catalog-json", "passed": 0, "total": 7}`; stderr `(empty)`; elapsed 0.9935 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py personal-status /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/personal-status/a --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/personal-status-a-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "personal-status", "passed": 12, "total": 12}`; stderr `(empty)`; elapsed 5.3666 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py personal-status /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/personal-status/b --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/personal-status-b-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "personal-status", "passed": 12, "total": 12}`; stderr `(empty)`; elapsed 5.4213 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py personal-status /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/personal-status-integrated-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "personal-status", "passed": 12, "total": 12}`; stderr `(empty)`; elapsed 5.8163 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py personal-status /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/personal-status-original-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 1; stdout `{"case": "personal-status", "passed": 0, "total": 12}`; stderr `(empty)`; elapsed 2.6744 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py project-check /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/project-check/a --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/project-check-a-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "project-check", "passed": 16, "total": 16}`; stderr `(empty)`; elapsed 7.1938 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py project-check /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/project-check/b --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/project-check-b-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "project-check", "passed": 16, "total": 16}`; stderr `(empty)`; elapsed 7.1664 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py project-check /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/project-check-integrated-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "project-check", "passed": 16, "total": 16}`; stderr `(empty)`; elapsed 7.6844 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit/experiments/openspec-pilot/evaluate.py project-check /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-original --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/final/project-check-original-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 1; stdout `{"case": "project-check", "passed": 0, "total": 16}`; stderr `(empty)`; elapsed 3.8331 seconds.

## Scope and limits

- This pass validates existing frozen attempts and the integrated feature source; it does not add actor attempts or change the original one-attempt-per-condition pilot design. Equal feature scores support a tie on this bounded probe set, without a general superiority or repeatability claim.
- These feature grades do not independently certify documentation quality, candidate-authored test quality, every possible alias/invalid-input/manifest combination, or whole-suite regression success. The controller reports the known full suite as 226 tests: 224 passed and 2 environment errors at `socket.socket` in `test_benchmark_revisions.OracleRegressionTests.test_native_git_inside_repository_stops_parent_discovery` and `test_native_grader_cannot_overwrite_protected_alias_target`. This verifier did not rerun that suite or treat either error as a product failure or passed check.
- Actor/evaluator filesystem isolation is not enforced. Each feature probe copies sources and supplies explicit fixture destinations; snapshots cover fixture paths and can detect persistent observed differences, not arbitrary external writes or transient writes that restore all observed state. Access times and file descriptors are not audited. Dynamic catalog probes deliberately modify fixture source files to exercise metadata/dependency validation.
- Bounded concurrent wall times are retained as execution receipts, not controlled performance benchmarks. Condition mapping was not used for scoring. No usage/cost or model-quality conclusion follows from this verification.
