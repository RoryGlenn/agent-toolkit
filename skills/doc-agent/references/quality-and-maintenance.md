# Review, validation, and maintenance

## Review according to reader impact

Start from the user's requirement and the actual reader's task. Separate a genuine defect from a stylistic preference. Technical accuracy and enough information to succeed come before polishing. Review a changed passage in enough surrounding context to catch contradictions without expanding a narrow request into a whole-site rewrite.

| Quality | Practical question |
| --- | --- |
| Accessible | Can this audience read and use it across relevant language, ability, device, and connection constraints? |
| Purposeful | Is the goal apparent, relevant, and achieved by the content? |
| Findable | Can the reader reach the right answer and recognize whether it applies? |
| Accurate | Does the content match supported behavior and current evidence? |
| Complete | Are the necessary prerequisites, actions, concepts, limitations, and next steps present? |
| Clear | Can the reader interpret relationships and actions without guessing? |
| Concise | Does the content avoid irrelevant material while preserving what success requires? |
| Consistent | Do terminology, structure, examples, and cross-page claims agree? |

An accurate useful page can tolerate imperfect prose. A polished page that sends the reader down an incorrect path needs correction first.

In a review, give the location, problem, reader consequence, evidence, and smallest useful correction. Use the project's severity convention if one exists; otherwise describe blocking, materially confusing, and optional improvements in plain language. Do not manufacture findings to fill categories. In edit mode, implement authorized fixes and report the significant ones.

## Evidence and validation

Choose checks according to the claim: source/API inspection for supported interfaces; safe execution for runnable procedures; format/render checks for layouts; observed user tasks for comprehension. Passing one does not establish the others. A lint pass does not prove technical accuracy, and a model role-playing a beginner is not a usability study.

For source conflicts, check version, release status, and which evidence describes actual behavior. Tests may be obsolete too. If a material conflict cannot be resolved, identify the exact unresolved claim and the smallest check needed; finish other useful work. Preserve confirmed working guidance instead of replacing it with speculation.

When execution is appropriate, use the documented starting state and avoid silently supplying missing expert knowledge. Log expected versus actual behavior and resulting reader friction. State what ran, under which conditions, what was observed, and what remains untested. Describe mock/fixture evidence as such. Do not convert a passing mock into a claim about a live service.

Documentation tests should exercise meaningful behavior: commands work from stated prerequisites, example outputs correspond to the input, and readers have a completion check. Avoid elaborate test infrastructure for a small wording edit.

## Feedback and measures

Use available support tickets, interviews, issue reports, and task observations to challenge assumptions. Keep qualitative evidence tied to its source and scope; do not invent representativeness or user quotes. Group repeated friction and distinguish documentation gaps, product defects, and individual support issues.

Turn actionable feedback into bounded changes. Look for duplicates, reproducibility, affected audience, and impact. Follow the existing issue workflow when asked; creating or posting external issues requires appropriate authorization.

Measure only when there is a decision to make. Relate organizational goals, reader goals, and documentation goals. Record a baseline when available and use related metrics plus qualitative evidence:

- A high bounce rate can mean a quick answer or failure to find one.
- More troubleshooting visits can mean more problems or better routing to useful help.
- Longer time on a page can mean engagement or confusion.
- More support cases can accompany a growing user population even when cases per user fall.
- Faster generation measures output speed, not reader success.

Time to first useful result, completion of a representative task, recurring misunderstandings, and unresolved issues can be useful signals. Do not invent measurements or start ongoing monitoring as part of an ordinary review.

## Change and maintenance

For a release or behavior change, identify the affected audiences, existing pages, examples, screenshots, conceptual explanations, reference entries, and migration paths. Update a coherent set within scope. Retain still-supported version guidance and make applicability clear.

Work through existing release and ownership mechanisms. Do not add a separate governance system when a current owner, issue, or checklist can do the job. Relevant maintenance tools include link checking, sample tests, prose linting, source-derived reference generation, and review-date reminders. A recent timestamp alone is not proof of accuracy; generated release notes still need user-impact editing.

For an information-architecture audit, inventory the relevant content and propose keep, review, merge, split, move, or retire decisions based on user needs and evidence. Validate common reader journeys. Preserve useful entry paths and plan redirects if moving published URLs. New metadata or machine-facing context is useful only when there is a consumer and an owner who can keep it current; AGENTS.md is not a guarantee of retrieval or grounding by every AI system.

Deprecation keeps needed guidance visible while explaining the change, alternatives, and migration. Deletion requires evidence that the content no longer serves its users and authorization for that action. Low traffic alone is insufficient. Replacing an expensive tutorial with a focused how-to may preserve support for the task while reducing maintenance.

## When specialist input helps

Flag the need for domain review, representative-user testing, localization, accessibility testing, or documentation expertise when the consequences and uncertainty justify it. Complete useful preparation and identify the precise gap. Do not turn every document into a mandatory sequence of reviewers or ask for approval that the user has already supplied.
