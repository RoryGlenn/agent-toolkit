# OpenSpec trial

This branch adds OpenSpec to Agent Toolkit itself and uses three CLI features to
test the workflow. The project intention remains in the main README. Feature
specifications describe concrete behavior within that intention; the trial does
not attempt to reverse-engineer a specification for the entire repository.

Read the [paired trial report](../../experiments/openspec-pilot/README.md) for the
comparison, retained candidate patches, checks, and limitations.

## Use the project workflows

On your Ubuntu machine, from this repository checkout, install the reviewed
OpenSpec CLI version **1.16.0** using the [official installation instructions](https://openspec.dev/docs/installation).
The matching generated Codex skills are already committed under `.agents/skills/`.
Verify the CLI, then refresh your coding-agent session:

```bash
openspec --version
openspec list
```

In Codex chat, describe the next substantial change:

```text
$openspec-propose Add JSON output to project integrity checks.
```

Read the proposed requirements and tasks. Correct any scope or behavior that
does not match your intent. Apply the change using its actual generated name:

```text
$openspec-apply-change <change-name>
```

Keep one implementation checklist in the OpenSpec change. The existing
issue-to-tested-pr, independent review, and verification guidance still governs
engineering work. Link the issue and PR to the specification instead of keeping
another copy of the acceptance criteria. Use DDIA, design, and documentation
skills when the change needs their expertise.

After implementation, independent review, and verification, archive the change
through OpenSpec so its requirements become part of the main specification.
Record unavailable checks explicitly. OpenSpec structural validation checks the
artifacts; tests and independent review establish different parts of correctness.

Routine small edits can continue through the existing lightweight process.

## Ownership and updates

| Material | Owner and update path |
| --- | --- |
| `.agents/skills/openspec-*` and the generated target marker | Upstream-generated dependency; refresh with the reviewed OpenSpec CLI |
| `openspec/config.yaml`, specifications, and change records | Project maintainers |
| `skills/` and `agents/codex/` | Existing toolkit catalog, routing, and authoring rules |
| `experiments/openspec-pilot/` | Frozen trial evidence and a standalone regrading script |

No wrapper skill or new named agent was added. OpenSpec's generated workflows are
project-local dependencies, outside the toolkit's installable catalog and
bootstrap ownership manifest. Project bootstrap does not install the OpenSpec
CLI, change global configuration, or copy these project workflows into consumers.

For an upstream upgrade, choose a reviewed release, run `openspec update` in this
project, inspect the generated diff, and repeat relevant checks. Keep local
project context in `openspec/config.yaml`; preserve upstream-generated skill
bytes. The [version and hashes](../../experiments/openspec-pilot/upstream.json)
record this trial's dependency identity. The [MIT notice](OPENSPEC-LICENSE) is
included unchanged from the release.

The adoption question in [issue #18](https://github.com/RoryGlenn/agent-toolkit/issues/18)
remains open: use the trial evidence to decide which overlapping custom planning
guidance can be retired. This pilot leaves the existing catalog workflows intact.
