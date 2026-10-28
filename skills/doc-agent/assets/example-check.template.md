# Example or procedure check

Use for a consequential example or reproducible workflow; a short inline note is sufficient for a small check.

| Item | Record |
| --- | --- |
| Reader and goal | Who is following the procedure and what they should accomplish |
| Source | Document section, example version, and supporting product evidence |
| Starting state | OS, shell, runtime and product versions, working directory, required files/packages/access |
| Isolation | Temporary directory, test fixture, or appropriate project environment; expected state changes |
| Substitutions | Placeholder values used and how a reader obtains their own values |
| Command or action | Exact safe action performed; no live secrets |
| Expected result | Observable success and relevant failure behavior |
| Actual result | Exit status, output, or inspected UI; state what was actually observed |
| Friction | Missing prerequisites, unclear meaning, unexpected behavior, or recovery gaps |
| Limits | Source inspection, mock, integrated test, live service, or human-user evidence; untested claims |

Do not extract and execute every fenced block. Distinguish commands, expected output, explanatory snippets, and destructive or externally mutating operations first.
