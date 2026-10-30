---
name: ddia-migrate-skill
description: Plan compatible schema, API, event, shard, and derived-state migrations. Use for backfills, rolling releases, reprocessing, cutover and rollback.
---

# DDIA Migrate Skill

For a top-level request outside this skill's domain, a mixed task, or a changed topic,
use the shared [task routing guidance](../task-routing-skill/SKILL.md) before applying
this procedure. Trivial requests need no routing workflow. An assigned specialist
subtask keeps its existing owner and scope; do not recursively reroute it.

Use the shared [DDIA Skill](../ddia-skill/SKILL.md), then the
[migrate procedure](../ddia-skill/references/workflows/migrate.md).
Read only the topic references relevant to the actual requirement.

The toolkit installer includes `ddia-skill` as this skill's dependency for both
personal installations and portable project copies. Resolve links relative to this
file, not the current directory. If manually copying files, copy both skill directories.
If shared resources are missing, disclose the incomplete installation and give only
bounded advice supported by the task evidence; do not claim the shared procedure or
original source was consulted. The host may run this workflow directly or delegate it to
`ddia_agent` when that named role is available. Keep the current implementation owner;
consultation and review are read-only unless sole write ownership was assigned.
