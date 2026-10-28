# Foundation and design intent

This skill is an original operational synthesis of *Docs for Developers: An Engineer's Field Guide to Technical Writing*, second edition (Apress, 2026), by Jared Bhatti, Sarah Corleissen, Jen Lambourne, David Nunez, and Heidi Waterhouse. E-ISBN: 979-8-8688-2509-5. It was developed from a full reading of the user-provided EPUB, including all eleven chapters, three appendices, code, tables, and substantive figures. The copyrighted book itself is not bundled or needed at runtime.

## Intentions and their roots

| Intention | Book foundation |
| --- | --- |
| Consistent style and wording | Chapters 3, 4, 9: predictable structure, editing, terminology, clarity, concision, consistency |
| Enough relevant detail, without distracting excess | Chapters 1–4 and 9: audience/task scope, content patterns, appropriate completeness |
| Transfer understanding instead of merely stating facts | Chapters 1–6: audience knowledge, concepts and procedures, explanation, examples, diagrams |
| Expose hidden assumptions | Chapters 1 and 4: curse of knowledge, research, friction logs, newcomer review |
| Make success and recovery observable | Chapters 3–5 and 7: procedure verification, examples, expected outputs, testing |
| Match content to the reader's situation | Chapters 1–3: user goals, personas, journeys, tutorial/how-to/concept/reference distinctions |
| Make useful information findable | Chapters 9 and 10: functional quality, titles, landing pages, navigation, deep-entry context |
| Preserve reliability as the product changes | Chapter 11: ownership, release alignment, versioning, maintenance |
| Convert repeated confusion into reusable help | Chapters 1, 8, 9: support evidence, feedback triage, qualitative and quantitative evaluation |
| Reveal underlying product friction | Chapters 1, 2, 5: friction logs, overly complex procedures and samples |
| Preserve useful reasons and constraints | Chapters 2 and 4: comments, conceptual documentation, technical accuracy |
| Serve varied abilities and circumstances | Chapters 1, 3, 6, 9: reading context, skimming, accessible media, language and performance |
| Improve or retire material based on usefulness | Chapters 9–11: contextual metrics, content inventories, deprecation, deletion |

The agent-specific workflow, evidence handling, permission boundaries, and invocation packaging are implementation decisions derived from these intentions and the user's instructions. They are not claimed to be a ready-made agent design supplied by the authors.

## Resolving common tensions

- **Complete versus concise:** include what the defined reader needs. API reference can require exhaustive coverage; a getting-started guide often needs one reliable path. Requested depth takes precedence over a generic brevity preference.
- **Consistency versus audience fit:** share terminology and patterns while changing the detail needed by a beginner, operator, integrator, or maintainer.
- **Understanding versus action:** explain enough to make significant choices and outcomes intelligible. Keep routine steps easy to follow; link optional background.
- **Shipping versus correctness:** ordinary imperfections need not delay useful publication. Incorrect or consequentially incomplete instructions require correction. Publication itself depends on the user's authorization.
- **Automation versus evidence:** AI can draft, edit, group feedback, and suggest gaps. It cannot establish a fact merely by generating it, and simulated readers do not establish real user success.
- **More content versus maintainability:** every page, example, diagram, and tool should justify its upkeep through user benefit. Reuse existing mechanisms and canonical content.

## AI guidance

The second-edition preface and Appendix B frame AI as assistance within a deliberate documentation process. Use product evidence and actual user research; review generated content and test generated samples. Keep prompts aligned with the intended audience, style, structure, and outcome. Structure content clearly for humans and machine consumers, and evaluate actual behavior rather than assuming metadata guarantees retrieval quality.

## Source cautions

The supplied EPUB contains erroneous figure alt text, obsolete fictional labels in some diagrams, an invalid date in sample JSON, inconsistent sample placeholders, and incomplete citation details. Accordingly, inspect figures and validate examples rather than reproducing them uncritically. Numerical perception/retention claims, research sample-size suggestions, and vendor/tool descriptions are publication claims, not universal rules or current capability guarantees. The agent retains the book's durable methods without encoding these defects or illustrative numbers as mandatory rules.
