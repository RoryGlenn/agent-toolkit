# Independent verification of frozen paired feature trial

Verified 2026-10-31. All six frozen candidates passed their held-out feature probes. The unchanged original source failed every feature probe through its unsupported-command positive controls. No candidate or evaluator code was modified by the verifier, no model/API calls were launched, no global environment/configuration changes were made, and no grading reruns were needed.

## Evaluator review and identity

- Original source HEAD: `0b36e7d4e95300b16a713edf831c8613dba46b69` at `/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit`.
- Pre-correction evaluator SHA-256: `cf8c5697bc123f8b70bcea6f6d2faacbd568e170ef9662ec74f2f4506b25e02f`.
- Reviewed scoring evaluator SHA-256: `eedafb2fd16561258b2631b952cc34b24179b9b5e2848f0b8f69cf5b4e50752b`.
- Review found that the first catalog JSON command and the first bootstrap-check/status positive controls ran before state snapshots. The verifier reported this to the controller rather than changing the evaluator or relaxing assertions. The controller added snapshots before and after those first inspections, and added `st_mtime_ns` to the existing inode/mode/content snapshots so same-bytes writes can be detected. All nine scoring runs used the corrected, stable evaluator.
- The evaluator hash matched before and after scoring. Frozen candidate directory hashes (paths, modes, mtimes, and regular-file contents or link targets) matched before and after scoring; detailed hashes are in `verification-run-receipts.json`.
- Case/slot names determined invocation only. Condition mapping was not used in grading, and both slots received the same probes.

## Scores

| Case | Slot a | Slot b | Unchanged original |
| --- | ---: | ---: | ---: |
| catalog-json | 7/7 | 7/7 | 0/7 |
| project-check | 16/16 | 16/16 | 0/16 |
| personal-status | 12/12 | 12/12 | 0/12 |

The six candidate evaluator processes exited 0, and the three unchanged-original evaluator processes exited 1 as expected. Every candidate probe was `passed`; there were no candidate failed probes, errors, timeouts, or missing grade artifacts. Original controls contain only `failed` probe results, not runtime `error` results.

Original failed probes:

- `catalog-json`: `contract`, `deterministic`, `human`, `readonly`, `dynamic-description`, `dynamic-dependencies`, `invalid-source`.
- `project-check`: `intact`, `edited`, `missing`, `block`, `unowned`, `source-change`, `malformed`, `unsafe`, `symlink`, `absent`, `unbootstrapped`, `conflict:--update`, `conflict:--dry-run`, `conflict:--all`, `conflict:--target codex`, `conflict:--skill documentation-skill`.
- `personal-status`: `intact`, `missing-home`, `missing-role`, `copied-role`, `atomic-source`, `role-symlink`, `foreign-skill`, `broken-skill`, `dependencies`, `copilot-all`, `custom-home`, `human`.

## Positive/negative controls and raw-output review

- Catalog probes first require `list --json` to return 0. The original returned argparse exit 2 for unsupported `--json`, so even its invalid-source rejection probe earned no credit. Both candidates produced one parseable JSON object equal to an inventory independently derived from the unchanged source, preserved baseline human output, reflected changed descriptions and dependency associations, and rejected invalid skill metadata with empty JSON stdout and an explanatory error.
- Each project probe first bootstraps a real installation and requires the new `--check` mode to accept it. The original returned argparse exit 2 for unsupported `--check` before any negative-state assertion, so none of its otherwise nonzero rejections earned credit. Both candidates reported 32 intact managed files. Raw errors named the edited/missing managed skill file, broken routing markers, malformed manifest, unsafe `../outside.txt` ownership path, and replaced symlink. Changes outside the routing block and extra unowned content passed, as did an upstream source-only change. All five conflicting options were explicitly rejected with exit 2.
- Each status probe first installs real links and requires the new status command to accept them. The original returned argparse exit 2 for unsupported `status`, preventing negative-probe credit. Both candidates reported the expected Codex role, selected skill, and routing dependency. For missing-home all three entries were `missing`; missing-role changed only the role to `missing`; copied-role, atomic source replacement, and role symlink changed only the role to `different`; foreign/broken skill links changed only the selected skill to `different`. The dependency selection reported `ddia-design-skill`, `ddia-skill`, `task-routing-skill`, and one deduplicated `ddia-agent.toml` role. Copilot `--all` reported all 15 catalog skills and no roles. Custom Codex home and human output passed. JSON entry order and schema assertions passed.
- Corrected filesystem snapshots compared names, inode identity, mode, mtime, contents, and symlink targets across source, destination, receipt and outside-link-target paths within each fixture. All applicable candidate non-mutation comparisons passed, including the first positive inspections. Read-only commands used explicit fixture destinations; subprocesses set only `PYTHONDONTWRITEBYTECODE=1` in their copied environment. `HOME` and `CODEX_HOME` were not set or replaced by this verifier.

## Exact evaluator invocations and results

Working directory for every invocation: `/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4`. The independent subprocess runner used a maximum concurrency of 3. All raw per-probe argv/stdout/stderr/exit results are in each `*-grade.json`; process-level stdout/stderr, timing, exact argv, and frozen hashes are in `verification-run-receipts.json`. No previous grading result was overwritten.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py catalog-json /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/catalog-json/a --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/catalog-json-a-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "catalog-json", "passed": 7, "total": 7}`; stderr `(empty)`; elapsed 2.6136 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py catalog-json /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/catalog-json/b --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/catalog-json-b-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "catalog-json", "passed": 7, "total": 7}`; stderr `(empty)`; elapsed 2.6755 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py catalog-json /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/catalog-json-original-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 1; stdout `{"case": "catalog-json", "passed": 0, "total": 7}`; stderr `(empty)`; elapsed 1.1473 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py personal-status /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/personal-status/a --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/personal-status-a-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "personal-status", "passed": 12, "total": 12}`; stderr `(empty)`; elapsed 6.1081 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py personal-status /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/personal-status/b --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/personal-status-b-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "personal-status", "passed": 12, "total": 12}`; stderr `(empty)`; elapsed 6.0924 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py personal-status /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/personal-status-original-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 1; stdout `{"case": "personal-status", "passed": 0, "total": 12}`; stderr `(empty)`; elapsed 2.8848 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py project-check /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/project-check/a --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/project-check-a-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "project-check", "passed": 16, "total": 16}`; stderr `(empty)`; elapsed 8.4069 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py project-check /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/frozen/project-check/b --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/project-check-b-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 0; stdout `{"case": "project-check", "passed": 16, "total": 16}`; stderr `(empty)`; elapsed 8.3356 seconds.

```sh
/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-evaluator.py project-check /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --baseline /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit --output /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/ab-pilot/evidence/project-check-original-grade.json --scratch-root /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp
```

Result: exit 1; stdout `{"case": "project-check", "passed": 0, "total": 16}`; stderr `(empty)`; elapsed 4.3936 seconds.

## Methodological limits

- This is one frozen attempt per case/condition and one execution of the held-out probe set. The result is a tie on these bounded feature contracts, with no estimate of repeatability and no general claim of superiority.
- These behavior grades do not independently certify documentation quality, candidate-authored test quality, every invalid-input/alias/selection combination, or full regression-suite success. Those checks must be reported separately by the controller.
- The existing full-suite baseline has two environment errors at `socket.socket` in `test_benchmark_revisions.OracleRegressionTests.test_native_git_inside_repository_stops_parent_discovery` and `test_native_grader_cannot_overwrite_protected_alias_target`. They are explicit verification limits, neither product failures nor passed checks. This verifier did not rerun or relabel them.
- Fixtures use copied sources and explicit local destinations, not enforced actor/evaluator filesystem isolation. They exclude `.git`, `.venv`, `.agents`, `openspec`, `books`, caches and logs. Snapshots cover the fixture tree, not arbitrary external paths, and cannot establish absence of transient writes that restore all observed metadata/content. Access times and file descriptors are not audited.
- Catalog dynamic-description/dependency and invalid-source probes intentionally modify fixture sources. They test dynamic catalog behavior and validation, rather than claiming those deliberate fixture changes are read-only operations.
- Timings are wall-clock measurements under bounded concurrent grading and are not controlled performance benchmarks. All API/model usage and cost comparisons remain outside this verifier scope.
