# Design

## Context

The pilot predates the README reorganization, legacy-code specialist, and existing
OpenSpec setup on main. Its historical experiment remains a separate frozen source state.

## Decisions

- Use main's README structure and retain all pilot usage, return-code, and ownership guidance.
- Retain the pilot's bounded-trial context in the otherwise empty main OpenSpec configuration.
- Keep experiment patches, logs, original source identities, and generated dependency bytes unchanged.
- Validate the integrated product separately; a current catalog includes newer main capabilities,
  so frozen catalog equality probes must use a baseline with the matching current inventory.

## Risks / Trade-offs

- Integration can silently lose newer catalog entries: verify legacy-code selection and dependencies.
- This host previously denied Bubblewrap loopback configuration: retain unavailable checks explicitly.
- Local integration does not update the hosted PR or establish hosted CI success.
