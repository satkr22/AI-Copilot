# Context-Aware Chunking Rules for Code RAG

## Purpose

This document defines industry-standard rules for creating
**context-aware code chunks** for Retrieval-Augmented Generation (RAG).
The objective is to maximize retrieval accuracy while preserving the
semantic meaning of source code.

The guiding principle is simple:

> **Chunk complete code entities, not arbitrary text.**

------------------------------------------------------------------------

# 1. Core Principles

A good code chunk must satisfy all of the following:

-   Represents one complete semantic unit.
-   Can be understood without reading the entire file.
-   Preserves structural context (file, scope, signature,
    documentation).
-   Is small enough for efficient embedding and retrieval.
-   Can be reconstructed back into the original source location.

Never split code purely by characters or lines.

------------------------------------------------------------------------

# 2. What Should Be a Chunk?

Use the Abstract Syntax Tree (AST) as the source of truth.

  Entity                Create One Chunk?
  --------------------- --------------------------------------
  Function              Yes
  Method                Yes
  Class                 Usually split into methods + summary
  Interface             Yes
  Enum                  Yes
  Struct                Yes
  Module summary        Yes
  Arbitrary 500 lines   Never

Example hierarchy:

``` text
auth_service.py
│
├── Module Summary
├── AuthService (summary)
│   ├── login()
│   ├── logout()
│   └── refresh_token()
└── helper_function()
```

Each function or method becomes an independent retrievable chunk.

------------------------------------------------------------------------

# 3. Required Chunk Structure

Every embedded chunk should contain contextual information before the
code.

``` text
FILE: src/services/auth/auth_service.py
LANGUAGE: Python
MODULE: auth.services

IMPORTS:
- jwt
- bcrypt
- UserRepository

PARENT SCOPE:
AuthService

ENTITY:
login(email: str, password: str)

DOCSTRING:
Authenticates a user and returns a JWT.

CODE:
def login(...):
    ...
```

This contextual text is what gets embedded.

------------------------------------------------------------------------

# 4. Metadata (Stored Separately)

These fields should be stored as vector database metadata rather than
embedded text.

  Metadata       Purpose
  -------------- ----------------------------
  repo_id        Repository filtering
  branch         Version awareness
  commit_hash    Exact snapshot
  language       Language filtering
  file_path      Source reconstruction
  entity_name    Exact lookup
  entity_type    Function, class, interface
  parent_scope   Class or namespace
  start_line     Citation
  end_line       Citation
  symbol_hash    Incremental indexing

Metadata enables hybrid retrieval and precise source reconstruction.

------------------------------------------------------------------------

# 5. Chunk Size Standards

Measure chunk size in **tokens**, not characters.

  Code Type                        Recommended
  ------------------ -------------------------
  Small utility                 80--250 tokens
  Normal function              200--500 tokens
  Complex function             500--800 tokens
  Large class          Split into child chunks

### Industry Recommendation

-   **Target:** 300--800 tokens
-   **Default maximum:** 512 tokens
-   **Upper practical limit:** 768 tokens
-   **Never exceed:** \~1000 tokens unless absolutely necessary

Why?

-   Smaller chunks improve retrieval precision.
-   Larger chunks dilute embeddings with unrelated logic.
-   512 tokens is a practical balance between context and search
    quality.

------------------------------------------------------------------------

# 6. Splitting Oversized Functions

Never split randomly.

### Incorrect

``` text
Chunk A
-------------
if user:
    ...
return result

Chunk B
-------------
else:
    ...
```

This destroys semantic meaning.

### Correct

Split only at logical AST boundaries.

``` text
process_order()

├── Chunk 1
│   Validation
│   Authorization
│
├── Chunk 2
│   Payment
│   Inventory
│
└── Chunk 3
    Notification
    Return
```

Each child chunk must still include:

-   Function signature
-   Parent class
-   File path
-   Docstring
-   Entity name

This allows every chunk to remain independently understandable.

------------------------------------------------------------------------

# 7. Parent--Child Retrieval Architecture

Production systems generally use two levels of chunks.

## Parent Chunk

Contains high-level context.

Example:

-   File summary
-   Class description
-   Imports
-   Public API
-   Relationships

Size:

-   **1,500--3,000 tokens**
-   Not usually embedded for primary retrieval

## Child Chunk

Contains executable logic.

Example:

-   One method
-   One function
-   One interface implementation

Size:

-   **200--500 tokens**

Retrieval flow:

``` text
User Query
      │
      ▼
Vector Search
      │
      ▼
Child Chunks
      │
      ▼
Load Parent Context
      │
      ▼
LLM Context Window
```

This provides precise retrieval without losing architectural
understanding.

------------------------------------------------------------------------

# 8. Overlap Rules

For AST-aware chunking:

**Default overlap = 0**

Reason:

Semantic entities already contain complete meaning.

Only introduce overlap when an entity is forcibly divided because it
exceeds the maximum size.

  Situation        Overlap
  ---------------- ---------------
  Function chunk   0
  Method chunk     0
  Class summary    0
  Forced split     30--80 tokens

Avoid sliding-window chunking for code.

------------------------------------------------------------------------

# 9. Context Inclusion Rules

Always include:

-   File path
-   Language
-   Module or namespace
-   Parent scope
-   Function signature
-   Docstring
-   Imports (only relevant ones)
-   Original code

Do **not** include:

-   Entire repository tree
-   Unrelated neighboring functions
-   Build artifacts
-   Generated files
-   Comments unrelated to the entity

Only include information that improves retrieval quality.

------------------------------------------------------------------------

# 10. Embedding Input Template

A recommended canonical template.

``` text
FILE: {file_path}

LANGUAGE: {language}

MODULE: {module}

PARENT: {parent_scope}

ENTITY: {signature}

DESCRIPTION:
{docstring}

IMPORTS:
{relevant_imports}

CODE:
{code}
```

This format is model-agnostic and works well across modern embedding
models.

------------------------------------------------------------------------

# 11. Retrieval Best Practices

Use a **hybrid retrieval pipeline**.

``` text
Repository
     │
     ▼
AST Parser
     │
     ▼
Semantic Chunks
     │
     ├── Embeddings
     └── Metadata
            │
            ▼
Hybrid Search
(BM25 + Vector)
            │
            ▼
Reranker
            │
            ▼
Top-K Chunks
            │
            ▼
Parent Context
            │
            ▼
LLM
```

Recommended retrieval stages:

1.  AST-based chunk generation
2.  Embedding creation
3.  Metadata indexing
4.  Hybrid search (BM25 + Vector)
5.  Cross-encoder reranking
6.  Parent context expansion
7.  LLM inference

------------------------------------------------------------------------

# 12. Rules Summary

## Always Do

-   Chunk by AST entities.
-   Keep one function or method per chunk.
-   Include structural context.
-   Store metadata separately.
-   Use 300--800 token chunks.
-   Use parent--child retrieval.
-   Preserve line numbers.

## Never Do

-   Split by characters.
-   Split in the middle of logic.
-   Embed entire files.
-   Mix unrelated functions.
-   Use large overlapping windows.
-   Lose file or scope information.

------------------------------------------------------------------------

# Default Production Configuration

  Setting             Value
  ------------------- --------------------------
  Chunking strategy   AST-aware
  Primary unit        Function / Method
  Target size         300--800 tokens
  Default max         512 tokens
  Hard limit          768 tokens
  Overlap             0
  Retrieval           Hybrid
  Reranking           Yes
  Parent context      Yes
  Metadata            Separate from embeddings

This configuration reflects the current industry-standard architecture
used by modern code retrieval and AI coding assistants, prioritizing
semantic correctness, retrieval precision, and efficient context
reconstruction.
