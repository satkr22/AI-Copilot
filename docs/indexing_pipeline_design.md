# Production-Grade Code Indexing Pipeline — Design Doc

Built directly on your uploaded `models.py`. Sections follow your numbering exactly. Full extended dataclasses are at the end.

---

## 1. Overall pipeline (mirrors Cursor / Copilot / Sourcegraph)

```
Discover files → Parse (tree-sitter) → Extract (queries → symbols + imports)
    → Gap-fill (cAST on uncaptured ranges) → Pack/Split (cAST on oversized symbols)
    → Structural enrichment (inline, free) → Persist to Postgres (files, symbols, imports, chunks)
    → [separate phase] Contextual enrichment (LLM, batched) → Embed → hybrid index (vector + BM25/trigram)
```

Everything up to and including "Persist to Postgres" is **your indexing pipeline** — the thing this doc designs. Embedding and hybrid retrieval indexes are the *next* phase (you said you'll do that after), but the schema below reserves the columns for it so you don't have to migrate later.

Discovery, before anything else: walk the repo respecting `.gitignore` (+ your own ignore list — `node_modules`, `dist`, `vendor`, `.git`), skip binary files, skip files above a size cap (e.g. >1–2MB — almost certainly generated/minified/vendored, not worth AST-chunking), and detect language from file extension + shebang for extension-less scripts.

---

## 2. Tree-sitter parse — what it actually gives you

`tree = parser.parse(source_bytes)` produces a **concrete syntax tree**, not semantics:

- Every node has a `type` (`function_definition`, `class_body`, `import_statement`, …), a byte range (`start_byte`, `end_byte`), and a point range (row/col).
- It's **error-tolerant** — a file mid-edit with a dangling brace still parses; broken regions surface as `ERROR` or `MISSING` nodes instead of failing the whole parse. Production pipelines check for these and either skip the offending subtree or fall back to a cruder split for that region — don't let one syntax error kill indexing for the whole file.
- It gives you **structure only** — no symbol resolution, no cross-file linking, no type info. "This identifier is a call to that function in another file" is not something tree-sitter tells you; that's a later graph-resolution step, out of scope for chunking.

This tree is the input to everything below. It's expensive to build (parsing dominates tree-sitter cost), so parse once and reuse the tree for query extraction, cAST, and gap detection — never re-parse for each step.

---

## 3. Tree-sitter queries via `.scm` — symbols and imports

One `.scm` file per language, using tree-sitter's tags-query convention (`@definition.*` / `@name` / `@import.*`). Example for Python:

```scheme
; symbols
(function_definition
  name: (identifier) @name) @definition.function

(class_definition
  name: (identifier) @name
  body: (block) @definition.class.body) @definition.class

(class_definition
  body: (block (function_definition
    name: (identifier) @name) @definition.method))

; imports
(import_statement) @definition.import
(import_from_statement) @definition.import
```

Running this via `Query.captures()` gives you a flat stream of `(node, capture_name)` pairs. Group each **match** (not each capture — a match is the whole pattern firing once) into one record:

- `@definition.function` / `@definition.class` / `@definition.method` → a symbol candidate. Pull `name` from the `@name` capture inside the same match, `start_byte`/`end_byte` from the outer `@definition.*` node (the whole function/class span, not just the identifier).
- `@definition.import` → an import candidate. Parse the node's own children for the module path, the imported name, and any alias (`as x`) — this part is language-specific since Python's `from x import y as z` and JS's `import { y as z } from 'x'` have different grammars, but the query only needs to mark the statement; a small per-language parser then pulls path/name/alias out of that node's children.

**What each query result should give you, concretely:** name, kind, byte range, and — separately, by walking a small distance from the matched node — signature (reconstruct from the function's parameter list node + return type node, not stored as a single string by tree-sitter), docstring (the string-literal or comment node immediately following/preceding, depending on language convention), and parent scope (which enclosing `@definition.class`/`@definition.function` this node's byte range falls inside — computed by containment check against already-collected symbols, not by the query itself).

Build this into the dataclass in section 11 (`SymbolDTO` / `ImportDTO`).

---

## 4. Output of step 3 for one file

A single in-memory (not yet persisted) result:

```python
@dataclass
class RawExtractionResult:
    file_path: str
    language: str
    tree: object              # the parsed tree-sitter Tree — kept only for this file's processing, not persisted
    source_bytes: bytes
    symbols: list[SymbolDTO]  # sorted by start_byte
    imports: list[ImportDTO]
```

Nothing here is written to Postgres yet — symbols/imports here are candidates that still need gap-filling and size-checking before they become final chunks.

---

## 5. cAST gap-finding — what's *not* captured by queries

Queries are selective: they only produce a result where a pattern matched. Top-level statements, module-level constants, code between imports and the first `def`, or a language construct your `.scm` doesn't cover yet — none of that shows up in step 4's `symbols` list.

Algorithm:

1. Take `symbols` sorted by `start_byte`, merge any overlapping ranges (methods are inside classes, so a class's range legitimately contains its methods' ranges — only *non-nested* symbols count as "claimed" at the top level).
2. Walk the file's full byte range `[0, len(source))` and compute the complement against the claimed top-level ranges — this gives you a list of `(gap_start, gap_end)` byte ranges.
3. For each gap, take the tree-sitter nodes whose byte ranges fall inside it (siblings at that level of the tree — e.g. top-level statements between two functions) and run cAST's **greedy-merge** over them: keep adding sibling nodes to a chunk while under the token budget, close and start a new chunk when the next node would exceed it. No recursion needed here in the typical case since gaps are usually small (imports, constants, a stray comment); if a single gap node is itself huge (e.g. a giant top-level dict literal or config block), recurse into it the same way you would an oversized symbol (step 7).

---

## 6. Turning gap code into a dataclass

Each gap chunk becomes a `CodeChunkDTO` with `chunk_type = ChunkType.GAP`, `origin = ChunkOrigin.CAST_GAP`, `symbol_ids = []` (no symbol owns this code), and no signature/docstring (there isn't one). Everything else (byte range, line range, raw content, language, file path) is populated the same as a symbol-derived chunk. This keeps gap chunks structurally identical to symbol chunks downstream — same table, same embedding pipeline, just a different `origin`/`chunk_type` tag so you can filter or weight them differently at retrieval time if you want (e.g. down-rank pure-gap chunks in ranking, since they're less likely to be "the definition of X").

---

## 7. Chunking — combining query symbols + cAST gaps, and splitting oversized symbols

One unified packing pass over **both** dataclasses together, walking the file in byte order:

```
for each item in sorted(symbols + gap_ranges, key=start_byte):
    if item is a gap chunk from step 6:
        emit as-is (already sized in step 5)
    elif item is a symbol and token_count(item) <= max_chunk_tokens:
        emit one chunk: chunk_type = symbol.kind, origin = QUERY_SYMBOL,
                         symbol_ids = [symbol.symbol_id], is_partial = False
    elif item is a symbol and oversized:
        # recurse into this symbol's own subtree (its body's children)
        # using plain cAST greedy-merge / recursive-split, capped at max_chunk_tokens
        sub_chunks = cast_split(symbol.node, max_chunk_tokens)
        for i, sub in enumerate(sub_chunks):
            emit chunk: chunk_type = symbol.kind, origin = QUERY_SYMBOL_SPLIT,
                        symbol_ids = [symbol.symbol_id],
                        is_partial = True, part_index = i, part_total = len(sub_chunks)
                        # each sub-chunk still inherits the parent's name/signature/docstring/scope_chain
```

Then a second pass merges **adjacent small chunks** (multiple one-line functions, a run of tiny gap chunks) whose combined token count is still under `max_chunk_tokens`, tagging the result `chunk_type = MERGED`, `origin = MERGED`, `symbol_ids = [all of them]`.

This is the exact combination discussed earlier: the query pass decides *where the preferred cuts are and what to call them*; cAST only ever runs on the parts the query pass couldn't bound on its own — gaps, and the insides of oversized symbols.

---

## 8. Each chunk's own dataclass

Final `CodeChunkDTO` (full field list in section 11) — one row per chunk, carrying its own copy of everything needed to reconstruct it and embed it without a join: file path, language, byte/line range, raw `content`, `enriched_content` (content + structural header — see section 10), lineage (`origin`, `is_partial`, `part_index`/`part_total`), `symbol_ids` it belongs to, `scope_chain`, and a `content_hash` for incremental re-indexing.

---

## 9. Getting chunks into Postgres

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector, for the embedding column you'll fill in next
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- trigram index, for hybrid lexical search later

CREATE TABLE files (
    file_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id         UUID NOT NULL,
    file_path       TEXT NOT NULL,
    language        TEXT NOT NULL,
    content_hash    TEXT NOT NULL,          -- whole-file hash; skip re-parsing unchanged files
    last_indexed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repo_id, file_path)
);

CREATE TABLE symbols (
    symbol_id        UUID PRIMARY KEY,
    file_id          UUID REFERENCES files(file_id) ON DELETE CASCADE,
    parent_symbol_id UUID REFERENCES symbols(symbol_id),
    name             TEXT NOT NULL,
    qualified_name   TEXT NOT NULL,
    kind             TEXT NOT NULL,
    start_byte INT NOT NULL, end_byte INT NOT NULL,
    start_line INT NOT NULL, end_line INT NOT NULL,
    signature   TEXT,
    docstring   TEXT,
    content_hash TEXT
);

CREATE TABLE imports (
    import_id   UUID PRIMARY KEY,
    file_id     UUID REFERENCES files(file_id) ON DELETE CASCADE,
    import_path TEXT NOT NULL,
    import_name TEXT,
    alias       TEXT,
    is_relative BOOLEAN DEFAULT FALSE,
    line_number INT
);

CREATE TABLE chunks (
    chunk_id           UUID PRIMARY KEY,
    file_id             UUID REFERENCES files(file_id) ON DELETE CASCADE,
    chunk_type          TEXT NOT NULL,
    origin               TEXT NOT NULL,
    symbol_ids           UUID[] DEFAULT '{}',
    scope_chain           TEXT[] DEFAULT '{}',
    start_byte INT NOT NULL, end_byte INT NOT NULL,
    start_line INT NOT NULL, end_line INT NOT NULL,
    content              TEXT NOT NULL,        -- raw source
    enriched_content     TEXT,                 -- + structural header (section 10)
    contextual_summary   TEXT,                 -- filled by the separate LLM enrichment pass
    is_partial           BOOLEAN DEFAULT FALSE,
    part_index           INT,
    part_total            INT,
    content_hash          TEXT NOT NULL,
    token_count            INT,
    embedding              VECTOR(1536),        -- filled by your embedding phase, not this pipeline
    UNIQUE (file_id, content_hash)               -- idempotent upsert on re-index
);

CREATE INDEX idx_chunks_trgm ON chunks USING gin (content gin_trgm_ops);
-- vector index (hnsw or ivfflat) added once you start populating `embedding`
```

Use `content_hash` as the natural idempotency key: on re-index, `INSERT ... ON CONFLICT (file_id, content_hash) DO NOTHING` — unchanged chunks never get rewritten or re-embedded, which is the Postgres-side equivalent of the Merkle-tree incremental indexing discussed earlier. Deleting a `file` row cascades to its `symbols`/`imports`/`chunks`, so a changed file is simplest handled as delete-and-reinsert at the file level, not a per-chunk diff.

---

## 10. Context-awareness — inline or separate?

Both — they're different costs, so they belong in different stages.

**Structural context (inline, free, part of this pipeline):** scope chain, signature, docstring, file path, imports in scope. You already have all of this from steps 3–7 — it costs nothing extra to compute, so build `enriched_content` right when you build the chunk, before it ever reaches Postgres:

```
# File: services/user_service.py
# Scope: UserService
# Signature: def get_user(self, id: str) -> User
# Imports: from db import Session

<raw content>
```

**Semantic context (separate batch step, before embedding, not before storage):** a short LLM-generated blurb situating the chunk within the whole file/repo — this is Anthropic's Contextual Retrieval technique: pass the full document plus the chunk to a fast model, generate a 1–2 sentence context ("this method is part of UserService, handling authenticated user lookups used by the login flow"), and prepend it before embedding. Anthropic's own benchmarks reported this — combined with BM25 hybrid search — roughly halved retrieval failure rates, with a further gain from adding a reranking step on top. Do this as a **separate batch pass over already-stored chunks** for two reasons: it's expensive (one LLM call per chunk) and only cheap with prompt caching (cache the whole file once, reuse across all its chunks' context-generation calls); and it shouldn't block or fail your indexing pipeline — if the LLM call fails or rate-limits, you still have a fully valid, retrievable chunk with structural context, just without the semantic blurb yet. Store the result in `contextual_summary`, and at embedding time embed `contextual_summary + enriched_content` (or just `enriched_content` if the summary isn't populated yet).

---

## 11. Top 15 languages (2026) to ship `.scm` files for

Ranking blends GitHub Octoverse contributor/repo-count data with real-world usage signals. TypeScript overtook Python and JavaScript to become the most-used language on GitHub by monthly contributors in August 2025 — the largest ranking shift in GitHub's history — and roughly 80% of new GitHub repositories in 2025 were written in just six languages: Python, JavaScript, TypeScript, Java, C++, and C#.

1. TypeScript
2. Python
3. JavaScript
4. Java
5. C++
6. C#
7. Go
8. C
9. Rust
10. PHP
11. Kotlin
12. Ruby
13. Swift
14. Shell / Bash
15. SQL

Treat rankings as directional, not exact — methodology varies by source (contributor count vs. repo count vs. survey usage), and this shifts quarter to quarter.

Separately, plan for **markup/config "languages"** you'll also want indexed but with a different query shape — HTML, CSS, JSON, YAML, Markdown, Dockerfile. These have no functions/classes, so their `.scm` files extract *tags* (keys, selectors, headings) rather than symbols, and — as noted earlier re: `go-code-chunker` — get zero `EdgeRules` (no call/import/inherit graph) since those concepts don't apply. Don't force them through the same symbol-extraction path; give them their own lightweight tags-only query and skip the oversized-symbol-split logic entirely (chunk by structural block instead — a YAML top-level key, a Markdown section).

---

## Complete dataclasses (extends your `models.py`)

```python
from dataclasses import dataclass, field
from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------

class SymbolKind(StrEnum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    INTERFACE = "interface"      # added — TS, Java, Go
    STRUCT = "struct"            # added — Go, Rust, C
    ENUM = "enum"                # added
    TYPE_ALIAS = "type_alias"    # added — TS `type`, Rust `type`


class ChunkType(StrEnum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"
    GAP = "gap"                  # added — cAST-only, no owning symbol (step 6)
    MERGED = "merged"            # added — multiple small chunks combined (step 7)


class ChunkOrigin(StrEnum):      # new enum — pipeline lineage, answers "how was this chunk built"
    QUERY_SYMBOL = "query_symbol"              # exact query match, fit under max size as-is
    QUERY_SYMBOL_SPLIT = "query_symbol_split"  # oversized symbol, cAST-split internally
    CAST_GAP = "cast_gap"                      # uncaptured code, filled by cAST (step 5/6)
    MERGED = "merged"                          # small adjacent chunks greedily merged


class ProviderType(StrEnum):
    JCODE = "jcode"
    SYMLENS = "symlens"


# ---------------------------------------------------------
# DTOs
# ---------------------------------------------------------

@dataclass(slots=True)
class SymbolDTO:
    symbol_id: str                    # added — stable id, e.g. uuid5(file_path + qualified_name + start_byte)
    name: str
    qualified_name: str               # added — e.g. "UserService.get_user"
    kind: SymbolKind
    language: str

    file_path: str                    # added — was missing; required once you're indexing >1 file
    start_byte: int                   # added — byte precision, needed for gap-diffing in step 5
    end_byte: int                     # added
    start_line: int
    end_line: int

    parent_symbol_id: str | None = None   # added — id-based FK, robust to duplicate/overloaded names
    parent_name: str | None = None        # kept from your original, for readability/debug

    signature: str | None = None      # added
    docstring: str | None = None      # added

    content_hash: str | None = None   # added — incremental re-indexing


@dataclass(slots=True)
class ImportDTO:
    import_id: str                    # added
    import_path: str
    import_name: str | None
    alias: str | None = None          # added — `import x as y`
    is_relative: bool = False         # added — `from . import x` vs absolute

    language: str = ""
    file_path: str = ""               # added
    line_number: int = 0
    start_byte: int = 0               # added
    end_byte: int = 0                 # added
    raw_statement: str | None = None  # added — full source line, useful for enrichment


@dataclass(slots=True)
class CodeChunkDTO:
    chunk_id: str                     # added — stable id for idempotent Postgres upsert
    chunk_type: ChunkType
    origin: ChunkOrigin                # added — lineage from step 7

    file_path: str                    # added
    language: str                     # added

    symbol_ids: list[str] = field(default_factory=list)     # replaces single symbol_name; supports 0..N
    symbol_names: list[str] = field(default_factory=list)   # kept for readability/debug
    scope_chain: list[str] = field(default_factory=list)    # added

    start_byte: int = 0                # added
    end_byte: int = 0                  # added
    start_line: int = 0
    end_line: int = 0

    content: str = ""                  # raw source (your original field)
    enriched_content: str | None = None    # added — content + structural header (section 10)
    contextual_summary: str | None = None  # added — filled by separate LLM enrichment pass (section 10)

    is_partial: bool = False           # added — True for oversized-symbol fragments
    part_index: int | None = None      # added
    part_total: int | None = None      # added

    content_hash: str = ""             # added — incremental re-indexing / idempotent upsert

    provider: ProviderType = ProviderType.JCODE
    token_count: int = 0


@dataclass(slots=True)
class ParseResultDTO:
    file_path: str                     # added
    language: str                      # added
    file_content_hash: str             # added — whole-file hash, skip unchanged files entirely
    symbols: list[SymbolDTO]
    imports: list[ImportDTO]
    chunks: list[CodeChunkDTO]
```

## What was missing and why it matters

- **`file_path` on every DTO** — your originals had none; once you're indexing a real repo (not a single file in isolation) this is required just to know what a symbol/chunk belongs to.
- **Byte offsets alongside line numbers** — line numbers alone aren't enough to compute gaps precisely (step 5) or to slice exact source text; bytes are unambiguous, lines are a display convenience on top.
- **Stable IDs instead of name-based linking** — `symbol_name` alone breaks the moment you have overloaded methods or two classes with a method of the same name; every DTO now carries its own id, and chunks reference symbols by id.
- **`content_hash` at symbol, chunk, and file level** — this is what makes re-indexing cheap: unchanged code hashes the same, so you skip re-extracting, re-chunking, and re-embedding it, mirroring the Merkle-tree incremental indexing discussed earlier.
- **`origin` / `is_partial` / `part_index` / `part_total`** — without this, a chunk from a split 900-line function is indistinguishable from a clean 40-line function at retrieval time, which matters if you ever want to weight or explain results.
- **`enriched_content` vs `content` vs `contextual_summary`** as three separate fields — you always want the raw source recoverable (`content`), separately from what actually gets embedded (`enriched_content`, optionally + `contextual_summary`), since the embedding text and the "show this to the user" text are not the same string.
