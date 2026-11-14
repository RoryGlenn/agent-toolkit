# Choose a useful safe-change boundary

Use the relevant section for the actual obstacle. These are applied decision aids from
Feathers' first edition; original sections are available through `scripts/book.py`.
The caller's requirements and language/runtime contracts remain authoritative.

## Characterize behavior and trace effects

Start with the intended edit, then follow values and effects through actual callers,
fields/aliases, collaborators, inheritance, globals, and external systems. Record where
the behavior can be observed. An effect sketch is a working hypothesis: check dynamic
dispatch, repeated calls, asynchronous work, errors, and cleanup that a simple arrow omits.

A useful boundary detects the plausible mistake. Choose inputs that distinguish changed
branches, numeric conversions, rounding, omitted calls, changed arguments, duplicate or
reordered writes, and changed default behavior. Whole-number examples can hide truncation;
matching a return value can hide a lost effect. If coverage says a line ran, verify it ran
on the relevant path and that the selected data makes an error observable.

Characterization records the observed baseline. A requirement states intended behavior.
An approved correction changes the expectation for an identified reason. Keep those
separate; snapshots of a defect do not grant it permanent authority. Investigate suspicious
behavior and dependent callers before changing it. Do not turn a bounded task into finding
and fixing every defect in the system.

A pinch/interception point can protect several related edits with fewer dependency breaks.
It is relative to those edits and effects, not a universal method every path crosses.
Check paths that bypass it. Broad covering tests can bootstrap protection, while narrower
tests improve localization and feedback where they are justified. A larger boundary is a
credible alternative when local isolation would cost more and detect less.

Source: chapters 1-3 and 11-13, especially
`OEBPS/html/ch13.html#ch13sec1lev1` and `#ch13sec1lev3`.

## Get construction and execution under control

Identify the exact blocker before choosing a technique:

| Obstacle | Candidate boundary | Questions to verify |
| --- | --- | --- |
| Constructor requires a difficult parameter | Supply a narrow value, adapter, interface, or dependency parameter | Which policy/representation moves to callers? Does production retain its default? |
| Constructor creates or configures an effectful dependency | Parameterized construction or an applicable factory seam | Can the test avoid the effect before it happens? Does constructor dispatch work in this language? |
| One method triggers an irrelevant external operation | Existing override boundary, or a minimal extracted call | What exactly is suppressed? Which required effects still need observation? |
| Many calls reach the same external/global object | Supplied collaborator, adapter, or a local getter | Is lookup timing/count/lifetime unchanged? Are any direct accesses left? |
| Needed behavior is buried in an unconstructable owner | Independent method object, responsibility, or a larger harness | Do reference/value semantics, per-call state, return and error behavior survive? |
| Procedural dependencies obstruct local execution | Actual link, function-pointer, preprocessing, or supplied-function seam | Which build/configuration selects the target, and how is the production target checked? |

Sensing and separation are different. A fake can expose arguments/state/order, whereas a
no-op merely removes a call. State what each test actually covers. Application tests using
a fake vendor adapter do not verify the adapter against the real vendor, the network, or
hardware; retain appropriate boundary/integration checks for those claims.

Be careful with tempting shortcuts:

- Passing null is a narrow test-only option when dereferences fail reliably and clearly in
  the actual language; it is unsuitable where it permits undefined or misleading behavior.
- Replacing a field after construction cannot prevent effects already performed by the
  constructor. Account for cleanup, aliases, and invariants dependent on the original object.
- Static setters and text replacement leave shared state. Restore it or isolate the process;
  do not let test configuration select fake behavior in production.
- A lazy getter changes creation timing. Check effects, identity, errors, concurrency,
  lifetime, and all direct accesses before calling that a preserving transformation.
- Publishing private methods can expose invalid states. Prefer the actual public path or
  a justified extracted responsibility; loosen access only where the boundary needs it.

Source: chapters 3-4 and 9-10; the technique catalog gives detailed alternatives and costs.

## Make the first incision and an urgent change

When no useful test can run before editing, explicitly separate the conservative bootstrap
from the behavior change. Keep the mechanical step small; preserve declarations and types,
inspect the exact diff, and use deliberate compiler/search/execution feedback. Compiler errors
can expose missed references but can also disappear into an inherited fallback or overload.
Independent review and a successful build reduce some risks; neither establishes all effects.

Under time pressure, compare a sufficiently small harness with sprouting new behavior into
a tested function/class or wrapping a protected unit. List the connection that remains
untested. A new helper can pass every unit test while its old caller never invokes it,
passes the wrong arguments, or invokes it in the wrong order. Check that connection and
the real production selection as soon as the available boundary permits.

For wrappers, protect before/after ordering, exceptions, repeated execution and cleanup.
For sprouts, protect the insertion point and state/alias assumptions. Retaining a temporary
scar is a trade-off toward control, not proof it is a desirable final interface. Avoid an
unrelated cleanup while the initial boundary is unprotected.

Source: chapters 2, 6, 8 and 23. The introduction and chapter 25 explicitly address
dependency-breaking steps performed before tests exist; do not rewrite that dilemma into
an impossible requirement that every bootstrap already have unit protection.

## Understand and improve the structure proportionally

Use sketches, focused inspection, and short notes to distinguish confirmed flow from
hypotheses. Disposable scratch refactoring can aid understanding only within authorized
write scope and isolation; a review-only task still returns advice without editing.
Explain an emerging responsibility through actual state and effect flow, including the
exceptions that do not fit the first story.

For a large class or method, compare the present change benefit of an extraction with its
new caller knowledge, construction/ownership cost, dispatch, and testing burden. Repeated
edits may reveal a shared responsibility; similar syntax alone does not prove common policy.
Keep convenient caller operations when extracting shared mechanics. A facade or a bounded
improvement can be an adequate stopping point.

Tests are part of the feedback system. Keep names, fixture state, and layout coherent with
the repository; do not reorganize every test to imitate a historical example. Verify the
actual test/build selection so helper/fake definitions do not enter production delivery.

Source: chapters 16-22 and the refactoring appendix. Chapter 24 emphasizes feasible local
progress under real constraints; a small protected area is not system-wide safety or an
answer to staffing/access constraints.

## Measure the feedback obstacle

Separate understanding time, edit/compile/link waits, test execution, and packaging. Measure
comparable edit-to-relevant-result cycles before claiming an improvement. A dependency
boundary may speed incremental builds and make clean rebuilds slower; report both. Book
timing targets, opinions about test categories, and anecdotal payoff are not measured
results for the current project. Use appropriate local unit and integration checks rather
than imposing a universal fraction-of-a-second threshold or excluding useful filesystem tests.

Source: chapters 2, 5 and 7. Historical tool names and code fragments illustrate mechanisms;
current repository behavior and current official tool documentation establish actual support.
