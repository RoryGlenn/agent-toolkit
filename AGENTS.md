# Toolkit contributions

For every new, modified, or imported toolkit skill or agent, follow the
[README naming convention](README.md#naming-convention-skills-and-agents).
The README is the naming authority; keep names and references consistent across the
artifact, metadata, installer associations, examples, and tests.

Use the [shared authoring standard](standards/authoring/README.md) for new, modified,
or imported skills and agents. Apply its relevant profile and update the adoption inventory;
do not require every package to use identical headings or read the standard at runtime.
Format checks do not establish behavioral quality or external community approval.
Use the standalone `skill_authoring` package for native scaffolding and upstream-based
evaluation. It is independent of the toolkit's custom skills, agents, and benchmark code.

Run the [development checks](README.md#development-checks) before completing a change.

For changes to a reviewed artifact, reassess affected contract and behavior claims, update
its linked review record and `reviewed_sha256`, and preserve explicit evaluation gaps.
Do not refresh a fingerprint without the assessment it represents.

New or changed toolkit entrypoints must participate in the shared task-routing contract.
Keep the policy in task-routing-skill, declare its dependency for new skill packages, and
verify selective installation plus routing outcomes separately from catalog validation.

Maintain only Codex TOML named-agent definitions. Portable skills may support other hosts,
but do not add or generate a second Copilot role format. Preserve historical receipt and
project ownership handling when retiring previously shipped role files.
