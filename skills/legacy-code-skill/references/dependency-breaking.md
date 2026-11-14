# Select a dependency-breaking technique

Use the actual obstacle and preserve its relevant behavior. This table is a decision map,
not a sequence or a mandate to add abstractions. Consult the original technique and nested
Steps section before a consequential attribution. Locators below are fragments in
`OEBPS/html/ch25.html`; the source helper returns complete hierarchical sections.

Every proposed seam needs a behavior location, enabling point, production selection, test
selection, and a check that each selection works. Independently verify the mechanics in
the actual language. Several printed snippets omit context or change expressions; they
are not executable equivalence proofs.

| # / source fragment | Technique and useful obstacle | Selection, cost, and protection |
| --- | --- | --- |
| 1 / `#ch25sec1lev1` | **Adapt Parameter:** an unmodifiable or wide incoming API obstructs construction/faking. | The caller supplies a narrow adapter or fake. Preserve real lookup/null/empty/value-selection behavior; the signature changes. Extract Interface can be simpler for an owned type. |
| 2 / `#ch25sec1lev2` | **Break Out Method Object:** useful work is trapped in an owner that is hard to construct. | A per-call object receives the original inputs and only needed owner access; the old entry forwards. Preserve alias/value semantics, state lifetime, effects, return and errors; avoid reusing stale per-call state. |
| 3 / `#ch25sec1lev3` | **Definition Completion:** severe compile/link dependencies block a C++ test executable. | Complete real declarations with alternate test definitions and exclude conflicting production bodies. Keep a separate test build; duplicate definitions, debugger confusion, and drift make this an initial wedge. |
| 4 / `#ch25sec1lev4` | **Encapsulate Global References:** related global data/functions need an owned boundary. | Initially preserve names/logic while grouping access; a further supplied-instance seam selects a fake. Grouping alone does not remove global state. Avoid moving substantial logic during the bootstrap. |
| 5 / `#ch25sec1lev5` | **Expose Static Method:** independent work cannot be reached without constructing an expensive owner. | Keep the old instance entry as a forwarder to same-input accessible static work. Check independence and dispatch/access costs; statics can be a staging point. The supplied example changes predicates, so use independently checked code. |
| 6 / `#ch25sec1lev6` | **Extract and Override Call:** one external call blocks the relevant execution. | A production wrapper forwards unchanged arguments to the real call; a testing subtype overrides it. Test override selection and effects that the no-op/fake leaves unprotected. |
| 7 / `#ch25sec1lev7` | **Extract and Override Factory Method:** internal creation/configuration is the obstruction. | A real factory retains creation; a test subtype supplies a fake. Check constructor dispatch: C++ base constructors do not select derived overrides, and other languages can expose uninitialized subtype state. |
| 8 / `#ch25sec1lev8` | **Extract and Override Getter:** replaceable access can defer internal creation. | An overridden getter selects a fake; the real getter lazily creates the dependency. Verify timing, identity, errors, concurrent access, ownership/destruction, and replacement of every direct access. |
| 9 / `#ch25sec1lev9` | **Extract Implementer:** callers need the existing type identity while its concrete implementation needs substitution. | Retain the original name as an interface and move concrete work to a production subtype; creation sites choose it or a fake. Audit construction, type/ABI, visibility and dispatch; the complex example is part of this technique. |
| 10 / `#ch25sec1lev10` | **Extract Interface:** a client needs only a small part of an owned collaborator. | Introduce the client-relevant operations and supply the real implementer or fake. Avoid mirroring the whole API. C++ conversion to virtual dispatch can change behavior; inspect subtypes and real selection. |
| 11 / `#ch25sec1lev11` | **Introduce Instance Delegator:** a static call prevents per-object substitution. | An externally supplied instance delegates to the old static behavior or is substituted. The delegator alone is insufficient without a selection point; harmless statics need no ceremony. |
| 12 / `#ch25sec1lev12` | **Introduce Static Setter:** an entrenched singleton/global factory needs test selection. | A setter selects the shared instance/factory while production keeps its default. Audit original instance disposal, lifetime and aliases; restore/isolate global state and prevent test selection from leaking. |
| 13 / `#ch25sec1lev13` | **Link Substitution:** language/build selection can replace an external definition. | The test executable/class path selects matching fake symbols; production selects real ones. Check signatures, linkage, selection order and required fake state; local fake tests do not verify the real library. |
| 14 / `#ch25sec1lev14` | **Parameterize Constructor:** internal creation prevents local construction. | Retain the old production constructor and add supplied-dependency construction. Check defaults, null/missing meaning and eager evaluation; a new parameter exposes dependency knowledge to clients. |
| 15 / `#ch25sec1lev15` | **Parameterize Method:** one call creates its own obstructive dependency. | Keep the old operation forwarding with original creation and expose an explicitly supplied variant. Preserve creation count/timing, argument evaluation, error behavior and caller coupling. |
| 16 / `#ch25sec1lev16` | **Primitivize Parameter:** a complex domain representation blocks testing under severe pressure. | Test useful work on a primitive intermediate representation and project/delegate from the domain boundary. Projection and hookup can remain untested; duplicated representation and split logic are explicit temporary costs. |
| 17 / `#ch25sec1lev17` | **Pull Up Feature:** a useful feature cluster can be separated from troublesome subclass dependencies. | Lift only the feature and required state into a base; real and testing subtypes supply remaining behavior. Check hidden state/dispatch and construction; this inheritance split is not automatically a good final responsibility boundary. |
| 18 / `#ch25sec1lev18` | **Push Down Dependency:** effectful operations can be moved out of the useful base behavior. | Production and testing subtypes supply the moved operations. No-op overrides do not protect omitted state changes or retry effects; an existing-method override may be smaller. |
| 19 / `#ch25sec1lev19` | **Replace Function with Function Pointer:** procedural callers need selectable behavior. | Production initializes a correctly typed pointer to the renamed original; tests choose a fake. Check initialization, ABI, lifetime, global restoration and concurrent use. Runtime pointer selection is not a zero-overhead compile-time guarantee. |
| 20 / `#ch25sec1lev20` | **Replace Global Reference with Getter:** one owner needs local substitution for repeated global access. | Production getter still resolves the original global; a test subtype supplies a fake. Preserve lookup count/timing and replace relevant direct paths. This does not necessarily introduce lazy construction. |
| 21 / `#ch25sec1lev21` | **Subclass and Override Method:** existing methods already supply useful separation/sensing boundaries. | Construct the appropriate real/test subtype. Verify actual overriding, access and existing subclasses; know which suppressed behavior remains outside the test. Prefer an existing sufficient boundary before an unprotected extraction. |
| 22 / `#ch25sec1lev22` | **Supersede Instance Variable:** replacement is possible only after acceptable original construction. | An explicit post-construction call installs the replacement. It cannot undo constructor I/O; audit disposal, aliases and derived invariants. Avoid ordinary production use that makes behavior depend on hidden replacement history. |
| 23 / `#ch25sec1lev23` | **Template Redefinition:** compile-time type substitution fits an already-template-heavy boundary. | Real/test template arguments select dependencies; an alias can preserve the old source name. Check actual type/ABI/overload contracts and real specialization. Header-visible implementation can worsen rebuild cost; measure it. |
| 24 / `#ch25sec1lev24` | **Text Redefinition:** the actual runtime/preprocessor permits controlled replacement. | Test load/preprocessing order selects the alternate method/text. Runtime replacement may persist for later tests; isolate or restore it and verify production load selection. The suppressed reporting operation remains untested. |

## Protect the real contract

Before adopting a mechanism, compare it with the nearest sufficient larger harness or
an existing seam. Record what the fake omits and which effects need separate protection.
For object ownership, verify creation, replacement, destruction, aliases, and configuration
carried by the old object. For dispatch changes, inspect inheritance, overload resolution,
virtual/non-virtual behavior, and all real creation sites. For build/text seams, check the
test and production artifacts select the intended definitions.

For a mechanical bootstrap, keep behavior change separate from moving or exposing code.
Compiler feedback is useful for missed references but does not establish values, order,
effects, concurrency, or correct production wiring. The book's chapter-8 and chapter-25
examples contain illustrative inconsistencies; preserve the intended source qualification
and test the actual proposed implementation rather than silently copying or repairing a
bug during a dependency-only change.

Chapter 25 has 25 nested second-level headings for 24 techniques: technique 9 includes
an additional complex example. Retrieve the whole technique to retain that discussion;
do not assume every technique has the same numbered Steps fragment.
