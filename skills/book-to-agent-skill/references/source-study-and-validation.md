# Source study and validation

Use the parts relevant to the current book and deliverable. This reference adds checks
that can be missed when moving from reading a book to building a reusable specialist.
It is not a requirement for a new platform, fixed document set, or elaborate review process.

Contents: source access; coverage and synthesis; operational translation; behavioral
evaluation; installation evidence.

## Reliable source access

Record the actual title, author, edition, format, and source identity. A local file can
be identified by a fingerprint; a hosted source may need a version or retrieval date.
Preserve stable chapter/section locators and a way to revisit the original. Check quoted
or attributed material against the identified edition, not another edition recalled from
memory. Keep source identity with derived notes so stale references can be recognized.

Inspect a few structurally different locations before selecting an extractor: an ordinary
section, a long section with a late qualification, and a relevant figure, table, formula,
or code sample. Compare the extraction with the original. Then establish that the chosen
mechanism covers the agreed source rather than assuming those samples prove completeness.

### EPUB

Inspect the package metadata, spine, navigation, and actual XHTML. Navigation may use NCX
or an EPUB navigation document. Headings may be nested containers or sibling paragraphs;
an anchor can resolve correctly while yielding only a heading and none of its argument.
Determine section boundaries from the actual document, including a section's final paragraph.

Check omitted or duplicate entries, same-file section boundaries, footnotes, and reading
order. Preserve meaningful code whitespace and identify image assets instead of claiming
their contents were interpreted as text. Resolve internal links as archive members and
reject external or escaping paths if writing a helper. Do not execute embedded content.

### PDF and scanned material

Use the available PDF skill/readers where appropriate. Check selectable-text quality,
column order, headers, footnotes, ligatures, code indentation, and tables. OCR can misread
numbers, operators, or negation; verify consequential passages against rendered pages.
Record PDF page index separately from printed page numbers when they differ. A diagram's
caption does not necessarily explain all information in the diagram.

### Plain text, Markdown, HTML, and other formats

Use existing reading/search mechanisms when they provide reliable complete access. Stable
headings or line references may suffice; a short text need not acquire a bespoke index.
For changing HTML, preserve a dated/versioned source when authorized. For other formats,
inspect the real structure before promising extraction or creating a generalized adapter.

### Repeated retrieval

When a helper is justified, keep it limited to the demonstrated source-access need. It
should make relevant material easy to discover and read completely, with explicit bounded
continuations and exact locators. If it stores an index, verify identity and content against
the source and fail clearly on stale, incomplete, or conflicting data. Preserve existing
files rather than silently replacing an incompatible library. Test section boundaries and
failure behavior with small original fixtures, then exercise the actual supplied book.

Source readers, indexes, and lookup commands do not prove that anyone studied the material.

## Coverage and synthesis

Choose a lightweight record that suits the source and existing workflow. Useful fields are:

| Information | What it establishes |
| --- | --- |
| Source identity and edition | Which text the analysis concerns |
| Agreed scope and source locations | What the study promised to cover |
| Reading status and reader | Which units received substantive attention |
| Visual checks and extraction limitations | Where text alone was insufficient |
| Chapter/section notes | Arguments, examples, and qualifications that were understood |
| Gaps, exclusions, and reconciliation | What remains unknown or was deliberately omitted |

Do not automatically mark every indexed unit as read. A reader's packet should connect
its conclusions to source locations and identify limitations. With multiple readers,
integrate their findings into a coherent model; concatenated summaries alone do not resolve
contradictions or cross-chapter dependencies. Keep enough source mapping to revisit a claim.

For each important idea, capture what problem it addresses, its causal explanation, required
conditions, illustrative cases, failure modes, and limits. Identify whether its support is
a proof, measurement, study, anecdote, heuristic, or opinion. Those categories need not be
formal labels on every sentence; preserve the distinction where it changes confidence.

Later chapters may narrow an early recommendation. Search for those qualifications and
compare related examples. Note source defects without silently teaching the defect as a
rule. Keep uncertainty visible when the source is ambiguous. The goal is usable judgment,
not a claim that a finite reading establishes perfect understanding.

## Translate understanding into operational guidance

Start from representative user tasks, not the table of contents. A specialist should know
what to inspect, what distinctions matter, which questions can change its answer, and what
evidence would justify a recommendation. Include the important exceptions and the option
to conclude that no change is warranted.

A useful conditional rule has the shape: given a particular problem and evidence, consider
a mechanism because it produces a stated benefit; retain specified obligations, acknowledge
the tradeoff, and choose another approach when its assumptions fail. This is a reasoning
pattern, not a mandatory output template.

Keep three layers distinct:

1. The source and detailed study preserve depth and provenance.
2. Selective references supply the details needed for the present task.
3. The operational skill and optional role define the job, decision process, and boundaries.

Do not copy every chapter into the role prompt. Conversely, a short prompt with no accessible
supporting knowledge cannot honestly claim complete book grounding. Use existing local
library conventions where possible; filenames and storage schemas may differ between books.
For a missing source, the agent should explain whether it has only derived notes or general
knowledge, and avoid invented page/section references.

Host-specific packaging belongs to the existing creator/installer conventions. Inspect
current supported formats rather than copying stale role options. Skills carry reusable
guidance; a thin wrapper is enough when a named role needs that guidance. Do not add a role
merely because another book package has one, or suppress a role explicitly requested by the
user. Preserve existing discovery and model behavior unless a change is part of the task.

## Independent behavioral evaluation

Choose a small set of tasks that distinguish useful judgment from slogan repetition:

- A representative application where a central idea helps.
- An exception where applying that idea mechanically would produce a bad recommendation.
- A case requiring no change, a qualified answer, or acknowledgement of insufficient evidence.

One realistic fixture may exercise more than one of these. The specialist's domain can
justify other cases; do not require identical fixtures or a fixed agent count for every book.

Give the acting agent the realistic request, skill/role, raw artifacts, and permitted scope.
Withhold the scoring rubric and expected conclusion. Use a separate evaluator or review
the observable result independently of the author. Check the decision, reasoning, cited
source, preservation of qualifications, and whether it completed the user's actual task.
Do not pass a result solely because it contains certain words, headings, or citations.

For software, executable control/failure cases can test the recommendation when appropriate.
For other domains, use suitable observable outcomes and subject-matter review. Tests must
stay within the authorized environment; simulated evidence remains simulated evidence.
An agent that creates files successfully has not thereby demonstrated domain competence.

Compare against an existing agent under comparable inputs only when claiming an improvement
over it. Otherwise report the narrower result actually established. Keep evaluation outputs
outside production projects and avoid creating a permanent evaluation service for a one-off
check. Save concise evidence when it will help reproduce or revisit the result.

## Installation and completion evidence

Run the target package's checks and any new executable. Use an isolated installation to
check selected resources, conflicts, repeat behavior, and restoration when the installer
supports them. Read back the actual installed files/links rather than relying on a success
message. Keep the selected source checkout stable if the installation links to it.

For a skill, verify host discovery and perform a task that loads the installed entrypoint
and its relevant resources. For a named role, also dispatch that exact role and verify that
it read the intended skill and source. A standard agent following the same instructions can
test the guidance but cannot prove custom-role discovery or dispatch. If the session caches
configuration, use a fresh session; disclose unavailable capabilities instead of guessing.

Keep these conclusions separate in the completion report: extraction works; the agreed
material was studied; the specialist handled the exercised tasks; the installed integration
works. Include exact checks and meaningful remaining limits. Claim a completed outcome only
to the extent supported by those separate observations.
