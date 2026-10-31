# Independent review: catalog-json and project-check

Reviewed baseline `0b36e7d4e95300b16a713edf831c8613dba46b69` and the four frozen candidate diffs. The review used the original acceptance criteria, patch contents, relevant source and tests, and repository AGENTS.md. No writer summaries, planning files, generated .agents/openspec files, or condition mapping were inspected. No implementation changes were made. At the assigning owner's explicit instruction, this assigned independent reviewer did not delegate further.

## Findings

1. **Medium — project-check/b accepts malformed source provenance and reports an intact manifest.**

   **Location:** `frozen/project-check/b/project_bootstrap.py:371`, `check_project`; its call to `validate_manifest` returns after checking the block hash at line 355 without validating `source`.

   **Invariant and consequence:** The acceptance criteria require malformed manifests to fail. The v1 manifest produced by `source_identity` and `bootstrap` includes `source.commit`, `source.dirty`, and `source.content_sha256`. Removing that object, replacing it with a string, or supplying wrong field types still produces status 0 and an integrity-intact diagnostic. This is a malformed-record false success; it does not bypass the individual owned-file hashes.

   **Reproduction:** Bootstrap a disposable project with `--skill documentation-skill --target codex`, retain every owned file and AGENTS block, and edit only `.agent-toolkit/manifest.json`. Each of these variants reproduced status 0, stdout `Project toolkit integrity intact: 32 managed files and routing block.`, and empty stderr:

   - remove `source`;
   - set `source` to `"corrupted"`;
   - set `source` to `{"commit": 7, "dirty": [], "content_sha256": "bad"}`.

   The same three probes against project-check/a returned status 1 with `Invalid source provenance in project manifest.`

   **Smallest safe correction:** Validate the recorded provenance object's shape and nullable commit/dirty values and SHA-256 syntax before returning a valid v1 manifest. This should use the recorded values only and must not compare them to today's toolkit source.

   **Current tests:** Not detected. The malformed-manifest variants in `tests/test_project_bootstrap.py` exercise schema, selections, ownership paths, and hashes, but omit source provenance. Add the three variants above to that table.

No material correctness or compatibility finding was identified in catalog-json/a, catalog-json/b, or project-check/a within this bounded review.

## Verification performed

All commands used `/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python` with `-B` and `TMPDIR=/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp`.

From each indicated frozen candidate directory:

| Candidate | Command after Python | Result |
| --- | --- | --- |
| catalog-json/a | `-m unittest discover -s tests -p test_install.py` | 49 passed |
| catalog-json/b | `-m unittest discover -s tests -p test_install.py` | 50 passed |
| project-check/a | `-m unittest discover -s tests -p test_project_bootstrap.py` | 29 passed |
| project-check/b | `-m unittest discover -s tests -p test_project_bootstrap.py` | 27 passed |

Additional disposable-project subprocess probes verified the malformed provenance finding above. Direct subprocess comparisons confirmed that each catalog candidate's default `install.py list` stdout is byte-for-byte identical to the baseline output. Code inspection traced JSON roles to validated runtime TOML names, direct dependencies to SKILL_DEPENDENCIES, CLI flag rejection before work, source-independent project checking, managed block hashing, and the existing ancestor/regular-file checks.

Reviewed patch SHA-256 values:

| Patch | SHA-256 |
| --- | --- |
| catalog-json-a.patch | `cce69434133d2569667167bf7659b870067270ae76d4ef7faab0b84163733d48` |
| catalog-json-b.patch | `470996f4406619a862eaca23a5929853ab6e3e135fd8ba7ff0af51f2b22a1a07` |
| project-check-a.patch | `1b70b05c70d451b8591ca962a815f33300139d49d1cb5c7ca3953e537c70fac4` |
| project-check-b.patch | `5032312d01023eab61b0b36dd0aa7b89b86763a2136f3238c4fc59091fefd9d7` |

## Comparative maintainability observations

- The catalog production implementations are effectively the same small addition: reuse validated inventory, resolve dependencies for availability, serialize direct dependencies and runtime roles, and branch only on the opt-in flag. Pretty versus compact JSON does not affect the contract. Neither introduces a new metadata store or changes human listing behavior.
- Catalog-json/b adds explicit missing-dependency and description-escaping cases and prevents even consulting Path.home in the list helper. Catalog-json/a makes its fresh-process no-cache proof more robust by removing inherited PYTHONDONTWRITEBYTECODE and PYTHONPYCACHEPREFIX first. These are complementary test strengths, not additional defects.
- Both project-check implementations reuse the existing safe read and block parsing helpers, accumulate managed-content failures, bypass current source inventory, and keep flag checking outside the operational path. That is a modest, understandable change in both candidates.
- Project-check/a validates provenance alongside the rest of the manifest and has a nested vendored-checker cache test; its check helper automatically asserts unchanged target snapshots for every call. Project-check/b supplies manifest-path context on parser failures and strengthens snapshots with mtimes, detecting same-inode rewrites that preserve bytes. Its provenance omission is the finding above.
- Neither test suite establishes crash consistency or concurrent filesystem substitution resistance. Those were already outside the read helper's guarantees and were not presented as new regressions.

## Unverified risks

This was a bounded CLI/source review with targeted existing/new tests and narrow probes, not a full repository development-check run. Windows path behavior, permission-denied reads under a non-root account, simultaneous filesystem changes, and upgrade histories from releases older than the supplied baseline were not executed. Managed-path symlink/special-file and marker handling were inspected and exercised to the extent covered by the candidate suites.

## Verdict

- catalog-json/a: `ready`
- catalog-json/b: `ready`
- project-check/a: `ready`
- project-check/b: `ready_with_corrections`
