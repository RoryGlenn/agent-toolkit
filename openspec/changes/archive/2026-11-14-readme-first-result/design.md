# Design

## Context

The documentation skill owns the defaults for direct use and for the Codex documentation
role. Its content patterns already distinguish onboarding from reference. The skill's
entrypoint is where the default needs to be explicit.

## Goals / Non-Goals

**Goals**

- Make the first useful result easy to reach with optional sections closed.
- Check the documentation a fresh session actually produces.

**Scope**

- The package's shared instructions, README evaluation, and review evidence.
- Keep the Pulse API reference case as a control. The standalone Doc Agent sync is follow-up work.

## Decisions

- Keep one rule in `SKILL.md` so the direct skill and role share it.
- Reuse the synthetic Roster CLI and sample. Supply optional migration and maintenance notes
  as source material and keep scoring criteria out of the writing session.
- Use a natural README prompt. Inspect the main reading path, execute the draft's example
  against the fixture, and grade the existing Pulse reference against its source.

## Risks / Trade-offs

A terse README can hide setup that readers need. Check the path with optional sections
closed and confirm the example's actual result. Fresh-session evidence is specific to
the tested fixture and host.
