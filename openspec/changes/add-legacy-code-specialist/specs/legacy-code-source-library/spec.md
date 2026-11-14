# Legacy code source library

## Purpose

Let the specialist consult the user's supported Feathers EPUB through a private local library with reproducible source identity, complete relevant section retrieval, and explicit failure behavior.

## ADDED Requirements

### Requirement: Initialize only a supported complete source

Initialization SHALL validate the book's identity and supported structure, record its source fingerprint, and require all 25 chapters before reporting success. Unsupported, malformed, or incomplete input SHALL fail without publishing an active partial library or replacing an existing one.

#### Scenario: Supplied supported EPUB is initialized

- **WHEN** the supplied EPUB has the expected identity and complete supported chapter structure
- **THEN** initialization creates a private local source and index with the book identity, source fingerprint, and available content locators

#### Scenario: Wrong book or missing chapter is supplied

- **WHEN** initialization encounters an unrelated book, unsupported layout, or missing required chapter
- **THEN** it reports the specific incompatibility and leaves any existing active library unchanged

### Requirement: Preserve existing source and private study

Repeated initialization with identical source and index SHALL be a no-op. Conflicting or incomplete existing state SHALL be refused with a useful explanation. Initialization SHALL preserve unrelated notes, study records, and user files.

#### Scenario: Source is initialized a second time

- **WHEN** the source and complete existing index match the supplied EPUB
- **THEN** the operation preserves their bytes and existing study files

#### Scenario: Existing library contains a conflicting index

- **WHEN** an existing source or index differs or only one exists
- **THEN** initialization refuses to overwrite it and identifies the conflict

### Requirement: Verify the source and complete derived index

Verification and source-dependent retrieval SHALL reject a changed source or altered derived content. Verification SHALL compare indexed text, boundaries, locators, and referenced assets with the source, including required coverage, rather than accepting the presence of a matching fingerprint alone.

#### Scenario: Derived text is altered without changing its recorded source hash

- **WHEN** indexed text or a section boundary is tampered with
- **THEN** verification and retrieval fail explicitly without presenting that index as source-grounded

### Requirement: Retrieve complete semantic sections

The library SHALL support chapter and section locators, including nested headings, technique steps, introductory text, and relevant supporting material. A section read SHALL include its subordinate content through the next heading of the same or higher level. Bounded reads SHALL expose continuation information without silently dropping content.

#### Scenario: Dependency-breaking technique has nested steps

- **WHEN** the caller reads one chapter-25 technique
- **THEN** its explanatory text, examples, qualifications, and nested steps remain within the result or its continuations
- **AND** the following technique is excluded

#### Scenario: A long section needs multiple reads

- **WHEN** a requested section exceeds the chosen output limit
- **THEN** the result identifies the locator and continuation position needed to retrieve the remaining content in order

### Requirement: Search and cite without inventing locations

The library SHALL support bounded literal search and chapter filtering, returning exact locators suitable for subsequent reads. Invalid queries and unknown locators SHALL fail clearly. Search snippets SHALL be identified as excerpts and SHALL NOT be presented as complete arguments or fabricated printed page citations.

#### Scenario: Relevant text is found in a chapter

- **WHEN** a literal query matches indexed content in the requested chapter
- **THEN** the result identifies the chapter, section, exact locator, and a bounded excerpt

#### Scenario: Locator does not exist

- **WHEN** the caller supplies an unknown fragment or chapter reference
- **THEN** retrieval reports the invalid reference instead of substituting unrelated text

### Requirement: Preserve meaningful source structure

Retrieval SHALL preserve meaningful code indentation, line breaks, ordering, and table relationships. It SHALL identify referenced figures and disclose presentation limits when plain text cannot convey source layout accurately.

#### Scenario: Code uses line breaks within inline markup

- **WHEN** the source encodes a multiline code example with nested markup and explicit breaks
- **THEN** retrieval preserves its line boundaries and significant whitespace

#### Scenario: An argument depends on a diagram

- **WHEN** retrieved text references a source figure
- **THEN** the result includes its exact asset locator so the caller can inspect the original image

### Requirement: Materialize only safe source assets

Asset access SHALL accept only known supported image members, verify their content, and write only within the library's private asset cache. It SHALL reject escaping references and unsafe destination links and preserve an existing divergent file.

#### Scenario: Known figure is requested

- **WHEN** a caller requests an indexed supported figure
- **THEN** the library returns a local verified image path within its own cache

#### Scenario: Asset path attempts to escape its boundary

- **WHEN** a reference or cache destination would escape the archive or approved cache, or overwrite unrelated content
- **THEN** access fails without writing outside that boundary or replacing the existing content

### Requirement: Keep source operations private and offline

Initialization, verification, search, reads, and asset access SHALL perform no network requests. Original EPUB content, extracted text, private study, and raw model traces SHALL remain outside published toolkit packages. Local storage SHALL use a private boundary; model-provider processing SHALL be described separately from offline retrieval.

#### Scenario: Package is installed without a personal library

- **WHEN** a user installs the portable skill or host role on another computer
- **THEN** no original book or private study is included and source-dependent commands report the missing local library

#### Scenario: Source is read through the local helper

- **WHEN** a caller requests a chapter or figure from an initialized library
- **THEN** the helper reads only local source/index/cache data without downloading or uploading material
