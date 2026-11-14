# documentation-onboarding Specification

## Purpose
Help a first-time reader understand what a repository offers and get a useful result from
its documentation.

## Requirements

### Requirement: Visible first-use path

When writing or substantially revising a repository README or getting-started guide, the
documentation skill SHALL default to one recommended path to a first useful result,
following the user's instructions and project conventions.

#### Scenario: Repository with optional setup and migration details

- **WHEN** a writer is asked to create a repository README from a working example and detailed migration and maintenance notes
- **THEN** a first-time reader can see the project's purpose, prerequisites, steps, example, and success condition with optional sections closed
- **AND** consequential warnings appear before the affected steps
- **AND** the reader can find optional guidance through links or expandable sections

### Requirement: Complete behavior reference

The documentation skill SHALL retain the full supported contract when writing API and CLI
references, including applicable inputs, defaults, results, and errors.

#### Scenario: Reference requested for an API operation

- **WHEN** an integrator asks for a concise reference from a supplied contract
- **THEN** the reference includes every supported parameter, its applicable constraints and default, and the documented success and error behavior
