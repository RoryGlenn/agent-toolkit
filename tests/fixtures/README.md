# Pre-routing project fixture

`pre-routing-project/` is the actual portable output of the unmodified installer from
commit `a143ea86a7a0e6fa4ce15ca3fecfe57b30aba308`, using an extracted Git archive and:

```sh
python3 /archive/install.py bootstrap --project /fixture/pre-routing-project --skill release-and-docs-skill
```

Its original version-one ownership hashes and instruction block are retained. The archive
has no Git root, so source commit/dirty fields are null. Tests copy this project into a
temporary directory and exercise the new dependency migration, including refusal paths.
The fixture's instruction text is test data, not contributor guidance.

## Pre-routing personal installation

`pre-routing-software/receipts.json` captures actual Codex and Copilot receipts produced
by that same archived baseline installer with `install --target HOST --skill
software-design-skill --home TEMP_HOME`. Only temporary home/source paths are replaced
with `__HOME__` and `__SOURCE__`. The original entrypoints are retained as link-identity
fixtures; unrelated book-retrieval resources are intentionally omitted because this test
does not execute the old skill. Tests replay the receipt into real symlinks/hard links,
then verify a new selected installation can be restored without changing those entries
or the old receipt. No baseline checkout or network access is needed when running tests.

## Retiring an owned Copilot project role

`pre-routing-copilot-project.json` captures the complete regular-file output and modes
from the baseline archive's `bootstrap --target copilot --skill documentation-skill`.
Tests materialize those original bytes, then verify the new skill-only target removes an
unchanged owned role, refuses a locally edited role, preserves an unmanaged role, and
retains the selected skills/host. This historical data is not a shipped agent definition.
