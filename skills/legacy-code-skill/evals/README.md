# Evaluate legacy-code guidance

The ten domain cases in [evals.json](evals.json) and two native integration cases in
[integration-cases.json](integration-cases.json) are original authored inputs. Their
existence is not a passing model result. See the [current assessment](../../../standards/authoring/reviews/legacy-code.md)
for the exact checked revisions, actual runs, failures, and remaining gaps.

LC01 protects export rounding, order, file effects, and audit-after-success. LC02 requires a
real construction-selection point, including a falsy fake. LC03 separates an approved
rounding correction from characterization of its defective baseline. LC04 exercises a
procedural boundary. LC05 is a trivial negative control; LC06-LC08 cover unavailable source,
tools, read-only scope and untrusted text. LC09 preserves data guarantees and one owner;
LC10 qualifies the untested connection between tested new code and its old caller.

`tests/test_legacy_code_suite.py` exercises trusted correct/wrong controls for the export,
construction, and discount contracts. They establish that the check can distinguish those
behaviors; they do not establish that a model will produce the right advice.
The export contract checks the candidate's successful audit and absence of a success audit
after a failed write; wrong controls retain correct bytes/returns while omitting or falsifying
those audit effects. Keep controller
expectations/oracles out of actor inputs. Do not execute arbitrary model output in the
controller's unrestricted process; use the verified native boundary for any execution.

Use the existing [authoring workflow](../../../skill_authoring/README.md). Its standard
adapter stages one runtime skill, with no sibling routing package, named roles, book library,
memories or grader answers. In-domain direct-use cases can run there with source absent in
both arms. LC05 uses implicit invocation. LC09's missing-capability disclosure is legitimate
in that standalone setup; it does not establish normally installed mixed-domain routing.

For the first matched pilot, select LC01, LC02, LC03 and LC05 before running: one paired
repetition gives eight attempts with a proposed 180-second actor deadline. Keep actual
model/effort, inputs, tools and source availability matched and retain setup failures and
timeouts. Use the existing signed-in CLI only within the current authorization; never add
API keys, weaken isolation, copy credentials into prompts or silently substitute a model.
Native canaries must pass before credentials are staged or an actor launches. Tool-network
denial is distinct from the CLI contacting its configured model provider.

Use separate disposable native host fixtures for LC11/LC12 and real named-role dispatch.
Install only the selected capability and routing dependency, preserve the task owner, and
inspect actual reads/events and final artifacts. A catalog entry, generic agent reading a
role file, or self-reported consultation is not proof of named-role execution. Book-backed
checks need an explicit private source boundary; the helper's `--data-dir` supports an
intentional allowed location. Never remove a user's real installation to simulate absence.

For any comparison, retain hashes, settings, attempt count, elapsed time, real usage where
available, full failures, and source-access differences. Provide equivalent original-source
and helper access when comparing guidance alone; otherwise label the intervention as a
package/source-access comparison. Use independent grading and the upstream report/blind
workflow where applicable. A single passing run is smoke evidence. Held-out work and
repetition remain necessary before broad reliability or superiority claims.
