# Documentation first-use assessment

Source baseline `3827a69364da2c89e770eedcf19866654fff8db8`. Assessed by the
implementation writer on November 14, 2026 for [issue #31](https://github.com/RoryGlenn/agent-toolkit/issues/31).
The [previous routing assessment](routing.md) retains its original runtime and evidence.

| Assessed file | SHA-256 |
| --- | --- |
| [Skill entrypoint](../../../skills/documentation-skill/SKILL.md) | `38f68dea9fbfd0d065f90360f10ab630b2c5e79e926a5a9c1bcfe10ac79b0223` |
| [Evaluation cases](../../../skills/documentation-skill/evals/evals.json) | `b972c440c5edd25379432b27bd60ae038f1bbb1381de819d8a0b83a7534167f0` |
| [Evaluation guide](../../../skills/documentation-skill/evals/README.md) | `5ef3304f5361e9a51668374904f6e259ad9fa6cad6d485ef70bf908c312bce9e` |
| [Roster maintenance input](../../../skills/documentation-skill/evals/draft/maintenance.md) | `b2b688b22fa43b641fa6c5f8267f04c779472064ad19bb696b18f829e08493f9` |

## Source assessment

| Check | Assessment |
| --- | --- |
| T01–T02 | Supported. The default applies to new or substantially revised repository READMEs and getting-started guides, subject to the user's requirements and project conventions. The natural README request exercises the intended writing path. |
| T03–T04 | Supported. The instructions call for a realistic example and observable success condition, put warnings with the affected steps, and preserve the supported API and CLI contract. The evaluation directs the grader to run the README's actual steps. |
| T05 | Supported as an authored case and recorded evaluation gap. Case 4 supplies working example inputs alongside migration and maintenance material. Case 3 keeps exact-reference completeness as a control. |
| T06, G01–G04 | Supported where applicable. The skill remains the existing direct and delegated entrypoint, with a compact instruction and the existing source, review, and authorization boundaries. The Codex role loads that same skill. |

## Evidence and limits

The evaluation loader accepted cases 1–4. Cases 1–3 match the source baseline.
Selective bootstrap and the integrity check passed for Codex, Copilot, and both hosts.
The installed Codex role points to the shared skill.

Two fresh sessions used Codex CLI 0.169.0, `gpt-6.1-sol` at medium effort, and only the
public fixture files. The standalone skill-authoring runner stopped at its local
sandbox preflight. The sessions used the existing benchmark isolation profile instead,
which passed all 18 checks for each session before launch. Tool traces show both
sessions read the candidate skill and its content patterns. An independent verifier
graded the outputs against the case assertions.

| Case | Observed result |
| --- | --- |
| 4, natural README request | The draft shows Roster's purpose, Python prerequisite, one copyable preview, and its expected result before optional material. Running the documented command from the stated directory exited 0 and returned `{"preview": true, "rows": 3, "duplicate_emails": 1}`. The input bytes stayed intact and the maintenance link resolved from the generated draft. |
| 3, Pulse reference | The draft covers all four parameters, their types and applicable defaults, the inclusive interval range, the 201 response with the effective values, and the 400 error with its fields. The draft leaves authentication and limits unspecified. |

The observed outputs were SHA-256
`859cebc2e355d0b228a827330943a60232b0fadc511a212094a81c9389c19666` for the README and
`344d67efb0d1911457aa915e0dc6785d996bda19f0ac8bb0a5fee2ecb4453b7c` for the reference.
These were direct-skill checks. Named-role execution, other hosts and models, comparative
quality gains, and real-reader outcomes still need evaluation.

Source verdict: **ready_with_limits**.
