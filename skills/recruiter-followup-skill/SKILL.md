---
name: recruiter-followup-skill
description: "Assess recruiter opportunities, audit response status across LinkedIn and email, and prepare or send requested replies without duplicates. Use for recruiter triage and follow-up, not general inbox cleanup or automatic job applications."
---

# Recruiter Follow-up Skill

Produce a clear next action for each relevant opportunity, supported by the actual conversation and any corresponding sent messages.

## Establish the current target

- Use the user's current role, employment, location, compensation, and timing preferences. Preserve full-stack/backend opportunities when AI is an additional interest. Do not silently retarget the search to AI-only roles.
- Distinguish base salary, total compensation, and on-target earnings. Unknown compensation or employment type is a qualification question, not evidence that a role meets or fails the target.
- Keep suitable, needs clarification, and unsuitable opportunities separate. Explain the specific mismatch when deprioritizing a lead.
- Prefer newer suitable leads and unanswered concrete questions; retain useful older conversations. Do not assume an advertised job is still open.

## Reconcile conversations

Prefer connected search/read tools; use the supported browser interface where required. Bound the audit by dates and sources, page through the relevant results, and disclose incomplete coverage.

For each opportunity, capture recruiter, employer/role, source links, message dates, latest incoming request, latest verified outgoing response, fit, and next action. Use an existing tracker or an in-session table; a new database or background service is unnecessary.

Match the same recruiter and opportunity across LinkedIn, notification emails, direct email, and any relevant careers mailbox. Inspect message bodies and actual outgoing records. An unread badge, viewed message, draft, calendar invitation, or previous assistant's completion claim does not establish a reply. A LinkedIn notification is a pointer to the conversation, not proof of its current state.

Distinguish:
- **Needs initial response:** no outgoing response found within the checked sources.
- **Needs follow-up:** earlier replies exist, but a newer request remains unanswered or the user's follow-up cadence is due.
- **Waiting on recruiter:** the latest substantive request came from the user.
- **Uncertain:** a relevant channel or part of the thread is inaccessible.

Use qualified wording when coverage is incomplete. Never infer that all worthwhile leads were answered from a sampled inbox.

## Reply when requested

An audit request authorizes reading and reporting. A request to answer the identified leads authorizes those routine replies; do not ask again for the same authorization. It does not authorize job applications, offer acceptance, new scheduled monitoring, or unrelated outreach.

Before sending, re-read the latest thread and check for an equivalent reply on another channel. Address the recruiter's actual question; do not request a job description or calendar link already provided. Use the user's writing style when available. Do not invent availability, qualifications, work authorization, compensation history, or an attached resume.

Send once, then verify the exact outgoing message, recipient/thread, and sent state. A send click or a transient 'Sending' indicator is insufficient. After an ambiguous send failure, inspect outgoing history before retrying. Report sent, drafted, and blocked items separately.

## Connection failure and resumption

Follow the selected tool's recovery documentation. Check available surfaces and try one documented recovery when appropriate. If the same startup/disconnection failure persists, stop dependent actions and continue useful drafting or evidence review. Do not loop on resets, promise a restart will fix the cause, or use hidden browser/session APIs.

Preserve a compact checkpoint in the existing task workspace or conversation: verified sends, uncertain attempts, remaining thread links, prepared copy, and the concrete connection blocker. Store only the personal information needed to resume. On reconnection, inspect current threads before sending anything; a queued draft is not a completed reply.
