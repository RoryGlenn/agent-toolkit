# Choosing content that serves the reader

Use only the pattern and checks needed for the current task. Existing user-supplied templates and explicit requirements remain authoritative; adapt these patterns instead of replacing a required structure.

## Content types

| Reader's need | Suitable pattern | Essential content | Common mismatch |
| --- | --- | --- | --- |
| Decide what a repository is and where to begin | README | Purpose, audience, quick start, prerequisites, links to deeper help, contribution/license information when relevant | An exhaustive manual that hides the starting point |
| Get a first useful result | Getting started | Brief goal, setup and access requirements, one working path, observable result, useful next step | Multiple advanced options before the first success |
| Learn an unfamiliar capability through practice | Tutorial | Learning objective, controlled setup/data, coherent end-to-end exercise, explanation of significant decisions, verification, transferable lesson | Assuming expertise the tutorial is supposed to teach |
| Complete a specific real-world task | How-to | Goal, applicability, prerequisites, ordered actions, necessary variations, success check, likely errors | Long conceptual history between essential steps |
| Understand how or why something works | Conceptual explanation | Core idea, relationships, a concrete example, boundaries and tradeoffs, link to application | A list of accurate facts with no account of what they mean together |
| Look up exact behavior | Reference | Consistent structure, names/types, required/default values, allowed values, effects, errors, versions, relevant examples | Omitting supported cases for brevity, or implying reference replaces onboarding |
| Diagnose and resolve a failure | Troubleshooting | Recognizable symptom/error, applicable context, diagnostic checks, likely cause when supported, corrective action, verification/escalation | Guessing causes or making a general FAQ the only route to an answer |
| Understand a release and act on changes | Release notes | User-visible change and impact, applicability/version, required action, migration and deprecation guidance, known limitations | An unedited list of commits without user impact |
| Maintain or modify an implementation | Developer explanation or code comment | Relevant intent, constraints, invariants, tradeoffs, reasons supported by evidence | Restating obvious syntax or inventing the author's intent |

Completeness depends on the selected job. Reference may need exhaustive supported parameters; a first-use guide usually needs one successful path. A user's explicit request for deep or exhaustive explanation is itself evidence about their needs.

For reference content, parameter names and types alone do not establish behavioral effects or every accepted value. If the contract omits an effect or validation constraint, keep it unspecified; do not invent an effect from a suggestive name or turn an unspecified string constraint into a promise that any string is accepted. Explain relationships the source does establish, such as defaults applying when optional parameters are omitted.

## Transferring understanding

Connect **meaning → consequence → action or judgment** where the connection helps the reader. For example, suppose a verified product rule is: “Uploads are asynchronous.”

- Fact alone: “Uploads are asynchronous.”
- Useful explanation: “Submitting an upload starts processing, so acceptance does not mean the file is ready. Check the upload status before using the result.”
- Task guidance requires the actual supported status command or interface, the completion signal, and relevant failure handling from source evidence. Do not invent those details to complete the example.

For a concept, explain the relationship that lets a reader predict behavior. For a procedure, explain consequential choices without interrupting every straightforward action. For a reference page, use structure to make distinctions visible. Test understanding with a relevant scenario or observable result when possible.

## Code samples

Choose examples for a real use case and the reader's language and experience. Prefer a small complete example over cleverness. Explain dependencies, environment, version, substitutions, how required values are obtained, and the effect of running the code.

- **Executable:** complete for its stated conditions; safe defaults; clear names; tested input and matching output; appropriate error behavior. Check clean-environment prerequisites when feasible.
- **Explanatory:** clearly identified partial code, schema, pseudocode, or response illustration. Show omissions explicitly. An ellipsis-containing response is not valid JSON for parsing.

Explain intent and product-specific behavior without narrating every obvious line. Preserve indentation, quoting, real identifiers, and copyability. Do not place prompt characters or output in a copyable command block unless distinguished. Avoid real secrets, misleading placeholder semantics, and assertions that code ran when it was only inspected.

Additional languages, interactive sandboxes, or sample generators incur maintenance work. Add them only when they serve the user's request and likely users. Reuse the project's sample source/tests instead of creating parallel copies when practical.

## Visuals

Use a visual when it explains something more efficiently: a screenshot locates an interface action; a box-and-arrow diagram shows relationships; a flowchart shows decisions; swimlanes show responsibility across a process. Keep the abstraction level and entry point clear. Label entities and relationships, apply shapes/colors consistently, and avoid color-only meaning.

Keep visuals adjacent to their explanation, readable at the intended size, and proportionate in file size. Inspect the actual asset, including labels and direction of arrows. Preserve editable source when creating or updating a visual. Important commands and values should remain selectable text.

Provide the image's relevant meaning in alt text or nearby text. Empty alt is appropriate only when the image is decorative or its full relevant meaning is already supplied accessibly; it is not a shortcut for complex diagrams. Video needs appropriate captions/transcript and a maintenance plan. Do not add a visual or video merely because a tool can produce it.

## Finding and connecting content

Choose the title and placement using users' vocabulary and likely entry paths. Support readers arriving directly at a deep page with applicability, prerequisites, and useful next steps. Prefer a canonical explanation linked from relevant contexts. Avoid duplicating content across multiple pages solely for convenience.

Use consistent patterns across related pages, but retain necessary differences. Sequences suit ordered tasks; hierarchies group related topics; cross-links connect contextual relationships. A landing page should route readers to useful destinations with few unnecessary decisions.
