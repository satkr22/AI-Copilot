# Refined MVP Plan: AI Software Engineer Copilot

## 1. Updated MVP Scope

Build a focused repository-aware **agentic AI engineering assistant** that demonstrates deep AI Engineering concepts without becoming a Cursor/Devin clone.

V1 must include:

- Repository upload via ZIP and public GitHub URL.
- Repository indexing with Tree-sitter.
- Metadata extraction for files, symbols, imports, function calls where feasible, APIs, modules, summaries, and repository statistics.
- PostgreSQL for structured repository intelligence.
- Qdrant for semantic code/document retrieval.
- Repository-aware chat with citations.
- One intelligent LangGraph workflow for planning, retrieval, tool use, validation, answer generation, and grounding.
- MCP-style local repository tools.
- Architecture overview with module map, dependency summaries, API overview, folder summaries, and Mermaid diagrams.
- Code suggestion workflow that returns proposed patches/diffs only.
- FastAPI backend, React frontend, Docker Compose deployment.

Keep V1 single-user. Skip login unless time remains.

## 2. Updated System Architecture

Use a modular monolith:

```text
React Frontend
  → FastAPI Backend
      → Project Service
      → Repository Import Service
      → Indexing Service
      → Repository Intelligence Service
      → Retrieval Service
      → LangGraph Agent Service
      → Code Suggestion Service
      → Architecture Analysis Service
      → MCP Tool Layer
  → PostgreSQL
  → Qdrant
  → Local Repository Storage
```

No microservices, Redis, Neo4j, Kafka, Kubernetes, or multi-provider LLM abstraction in V1.

This architecture is valuable because it shows production layering while staying buildable by one developer.

## 3. Updated Repository Intelligence Pipeline

Pipeline:

```text
Upload/import repository
→ Normalize repository path
→ Ignore generated/vendor folders
→ Detect languages/frameworks
→ Parse supported files with Tree-sitter
→ Extract files, symbols, imports, exports, routes, classes, functions
→ Extract lightweight function call relationships where feasible
→ Build chunks by symbol/file section
→ Generate file summaries
→ Generate module summaries
→ Generate dependency summaries
→ Generate architecture summary
→ Generate repository statistics
→ Store metadata in PostgreSQL
→ Store embeddings in Qdrant
```

Add richer intelligence without adding graph infrastructure:

- `file_summary`: short natural-language summary of file purpose.
- `module_summary`: summary per top-level package/folder.
- `dependency_summary`: human-readable summary of internal/external dependencies.
- `function_calls`: best-effort static calls from Tree-sitter queries.
- `exported_apis`: HTTP routes, exported functions/classes, public interfaces.
- `repo_statistics`: language breakdown, file count, symbol count, top modules.
- `architecture_summary`: generated from folder structure, imports, APIs, and summaries.

Function call extraction should be best-effort, not perfect. That keeps it realistic.

## 4. Updated LangGraph Workflow

Use one intelligent graph, not many fake agents.

```text
classify_intent
→ plan_context
→ retrieve_initial_context
→ context_validation
    → if insufficient: retrieve_more
    → if sufficient: continue
→ tool_selection
→ tool_execution
→ generate_answer_or_patch
→ grounding_check
→ response
```

Intent types:

- repository question
- semantic search
- file/function explanation
- architecture explanation
- debugging help
- documentation generation
- code suggestion

Agentic behavior:

- Decides what context is needed.
- Chooses semantic search, symbol lookup, file read, architecture summary, or dependency lookup.
- Retrieves more context if initial context is weak.
- Uses tools only when needed.
- Rejects or qualifies answers when repository evidence is insufficient.
- Produces citations from real files/symbols.

This is genuinely agentic while staying simple.

## 5. Updated MCP Tool Design

Implement local MCP-style tools first:

- `repo.semantic_search(project_id, query, top_k)`
- `repo.keyword_search(project_id, query)`
- `repo.search_symbols(project_id, query, kind?)`
- `repo.read_file(project_id, path, start_line?, end_line?)`
- `repo.get_symbol(project_id, symbol_id)`
- `repo.get_file_summary(project_id, path)`
- `repo.get_module_summary(project_id, module_path)`
- `repo.get_dependencies(project_id, file_or_module)`
- `repo.get_architecture_summary(project_id)`
- `repo.get_api_overview(project_id)`

These tools demonstrate MCP/tool-use concepts without depending on external services.

External MCP integrations like GitHub issues, terminal execution, Slack, Jira, or docs retrieval are V2.

## 6. Updated Retrieval Pipeline

Use practical hybrid retrieval:

```text
User query
→ Intent-aware retrieval plan
→ Qdrant semantic search
→ PostgreSQL symbol/path/API lookup
→ Optional keyword search
→ Optional dependency/call relationship expansion
→ Rerank/deduplicate
→ Validate context sufficiency
→ Retrieve more if needed
→ Send compact cited context to LLM
```

Keep retrieval transparent. Return:

- file path
- symbol name
- line range
- relevance reason
- source type: semantic, symbol, dependency, API, summary

Do not add BM25 infrastructure unless PostgreSQL full-text search is easy within time.

## 7. Updated Code Generation Flow

Code generation should be an engineering workflow, not a single prompt.

```text
User code request
→ classify as code_suggestion
→ planner identifies affected areas
→ retrieve relevant files/symbols/patterns
→ inspect existing style and dependencies
→ generate proposed change
→ validate against repository context
→ return unified diff/patch + explanation
```

V1 behavior:

- Return proposed patch only.
- Do not automatically edit files.
- Mention files that would change.
- Explain why the change fits existing architecture.
- Reuse existing services/classes when discovered.
- Warn when context is insufficient.

This gives strong interview value without dangerous autonomous coding loops.

## 8. Updated Architecture Analysis Flow

Generate architecture insights from extracted metadata:

```text
Repository metadata
→ Folder/module grouping
→ Import relationship analysis
→ API route extraction
→ Service/dependency grouping
→ Module summaries
→ Architecture summary
→ Mermaid diagrams
```

V1 architecture outputs:

- Repository map.
- Folder/module summaries.
- Main languages/frameworks.
- Internal dependency overview.
- API endpoint overview where detectable.
- Mermaid module dependency diagram.
- “How this project is organized” explanation.

No Neo4j. Store relationships in PostgreSQL and query them directly.

## 9. Updated Folder Structure

```text
AI_Copilot/
  backend/
    app/
      api/
        routes/
      core/
      db/
      models/
      schemas/
      services/
        projects/
        repositories/
        indexing/
        intelligence/
        retrieval/
        architecture/
        codegen/
        chat/
      ai/
        graphs/
        prompts/
        tools/
        mcp/
        evaluators/
      workers/
      main.py
    tests/
    alembic/
  frontend/
    src/
      pages/
        Projects/
        RepositoryImport/
        RepositoryExplorer/
        Search/
        Chat/
        Architecture/
        CodeSuggestions/
      components/
      api/
      stores/
      types/
  storage/
    repositories/
  docker-compose.yml
  docs/
```

## 10. Updated Database Schema

Core tables:

- `projects`: name, description, status, created_at.
- `repositories`: project_id, source_type, source_url, local_path, branch, commit_hash, indexed_at.
- `indexing_jobs`: project_id, status, progress, current_step, error_message, started_at, finished_at.
- `files`: repository_id, path, language, hash, size, summary, line_count.
- `chunks`: id, file_id, symbol_id, content, start_line, end_line, chunk_type
qdrant_point_id
- `symbols`: file_id, name, kind, signature, start_line, end_line, summary.
- `imports`: file_id, imported_module, resolved_file_id nullable, is_external.
- `function_calls`: caller_symbol_id, callee_name, callee_symbol_id nullable, file_id, line_number.
- `api_endpoints`: file_id, method, path, handler_symbol_id nullable, framework nullable.
- `modules`: repository_id, path, name, summary.
- `module_dependencies`: source_module_id, target_module_id, dependency_count.
- `chunks`: file_id, symbol_id nullable, chunk_type, content, start_line, end_line, qdrant_point_id.
- `repo_statistics`: repository_id, json_data.
- `architecture_summaries`: repository_id, summary, mermaid_diagram, generated_at.
- `chat_sessions`: project_id, title, created_at.
- `chat_messages`: session_id, role, content, citations_json, created_at.
- `code_suggestions`: project_id, user_request, patch, explanation, status, created_at.

The files table stores a short summary for each file, which is useful for UI and structured lookups. The text that gets embedded (the chunk content itself) should also be stored in PostgreSQL in a chunks table (or an equivalent)
Then:
- PostgreSQL stores the actual chunk text and its metadata.
- Qdrant stores the embedding of that chunk plus a small payload (IDs, file path, line range).

This design keeps PostgreSQL as the source of truth while Qdrant serves as the fast semantic index. It also makes re-embedding easy if you switch embedding models later—you can regenerate vectors from the stored chunk content without reparsing the repository.

Use JSON for flexible statistics and citations. Use relational tables for files, symbols, imports, APIs, and calls.

## 11. Updated API Design

Projects and repositories:

- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/repositories/upload`
- `POST /projects/{project_id}/repositories/import-github`
- `POST /projects/{project_id}/index`
- `GET /projects/{project_id}/indexing-jobs/latest`

Repository intelligence:

- `GET /projects/{project_id}/files`
- `GET /projects/{project_id}/files/{file_id}`
- `GET /projects/{project_id}/symbols`
- `GET /projects/{project_id}/modules`
- `GET /projects/{project_id}/statistics`

AI features:

- `POST /projects/{project_id}/search`
- `POST /projects/{project_id}/chat`
- `POST /projects/{project_id}/explain`
- `GET /projects/{project_id}/architecture`
- `POST /projects/{project_id}/architecture/regenerate`
- `POST /projects/{project_id}/code/suggest`
- `POST /projects/{project_id}/docs/generate`

## 12. Updated Weekly Roadmap

Week 1:

- Set up FastAPI, React, PostgreSQL, Qdrant, Docker Compose.
- Add project/repository models and APIs.
- Build basic frontend dashboard.

Week 2:

- Implement ZIP upload and public GitHub import.
- Add indexing job tracking.
- Add repository storage and ignore rules.

Week 3:

- Implement Tree-sitter parsing for Python and TypeScript/JavaScript.
- Extract files, symbols, imports, APIs, and best-effort function calls.

Week 4:

- Add chunking, embeddings, Qdrant indexing, semantic search.
- Add repository explorer and search UI.

Week 5:

- Add file summaries, module summaries, repo statistics, and architecture summary.
- Add architecture page with Mermaid diagram.

Week 6:

- Implement LangGraph workflow with context validation, retrieve-more loop, tool selection, grounding check.
- Add chat UI with citations.

Week 7:

- Add code suggestion workflow returning patches.
- Add documentation generation if time allows.
- Add tests for indexing, retrieval, and graph workflow.

Week 8:

- Polish UI and demo flows.
- Add Docker/AWS deployment docs.
- Prepare README, architecture docs, demo script, and resume bullets.

## 13. Updated Feature Priority

Must have:

- ZIP upload.
- Public GitHub import.
- Tree-sitter repository indexing.
- File/symbol/import/API extraction.
- Best-effort function call extraction.
- PostgreSQL metadata store.
- Qdrant semantic retrieval.
- Repository-aware chat with citations.
- One LangGraph agentic workflow.
- MCP-style local tools.
- Architecture overview.
- Repository explorer/search UI.
- Docker Compose.

Nice to have:

- Code suggestions as patches.
- Documentation generation.
- Mermaid dependency diagrams.
- Module dependency visualization.
- Debugging assistant mode.
- Test generation suggestions.

Future:

- Private GitHub OAuth.
- PR review.
- Automatic code edits.
- Terminal execution.
- External MCP servers.
- S3 storage.
- Redis queue.
- Neo4j graph database.
- Multi-agent workflows.
- IDE plugin.
- Kubernetes/ECS.

## 14. Feature Evaluation

| Feature | Value | Interview Impact | Realistic? | V1/V2 |
|---|---:|---:|---:|---|
| Tree-sitter indexing | Very high | Very high | Yes | V1 |
| Qdrant semantic search | Very high | Very high | Yes | V1 |
| PostgreSQL metadata | Very high | High | Yes | V1 |
| LangGraph workflow | Very high | Very high | Yes | V1 |
| MCP-style tools | High | Very high | Yes | V1 |
| Module/file summaries | High | High | Yes | V1 |
| Function call extraction | Medium-high | High | Best-effort | V1 |
| Architecture diagrams | High | High | Yes | V1 |
| Code patches | High | High | Moderate | Nice-to-have V1 |
| Docs generation | Medium | Medium | Yes | Nice-to-have V1 |
| Test generation | Medium | Medium | Yes | Nice-to-have |
| Private GitHub | Medium | Medium | Time-consuming | V2 |
| Neo4j | Low for MVP | Mixed | Adds complexity | V2 only if needed |
| Redis | Low for MVP | Low | Unnecessary | V2 |
| Multi-agent system | Low for MVP | Risky | Too much | V2 |
| Kubernetes | Low | Low for this goal | Too much | Exclude |

## 15. Risks and Simplifications

Risks:

- Tree-sitter support can grow too large.
- Function call extraction can become complex.
- Code generation can drift toward autonomous coding.
- Architecture analysis can become vague if metadata is weak.
- UI polish can consume too much time.

Simplifications:

- Support only Python and JavaScript/TypeScript first.
- Treat function calls as best-effort static metadata.
- Return proposed patches, never auto-apply them.
- Use PostgreSQL JSON for flexible summaries/statistics.
- Use one LangGraph workflow.
- Use local MCP-style tools before external MCP servers.
- Keep auth out of V1 unless the core demo is complete.

## 16. Future V2 Roadmap

V2 should add depth only after V1 is complete:

- Private GitHub OAuth and repository sync.
- PR review workflow.
- External MCP integrations: GitHub, terminal, docs.
- Test generation with framework detection.
- Controlled patch application with human approval.
- Incremental re-indexing by file hash.
- S3 repository storage for AWS deployment.
- Redis or a real worker queue only when background jobs need it.
- Neo4j only if relationship traversal becomes central.
- IDE extension after the web app proves the core workflow.
- Multi-agent workflows only for clearly separate tasks like review, testing, and documentation.

## Final Positioning

This refined V1 should be presented as:

> A production-quality repository intelligence and agentic RAG system for software engineering tasks, built with FastAPI, React, LangGraph, LangChain, Tree-sitter, PostgreSQL, Qdrant, MCP-style tools, and Docker.

The project’s interview strength is not feature count. It is that every major piece demonstrates a modern AI Engineering concept in a clean, buildable, explainable way.

## Workflow Diagram:

                    User
                      │
                      ▼
             LangGraph Planner
                      │
          ┌───────────┼────────────┐
          │           │            │
          ▼           ▼            ▼
    Semantic      Symbol/API    Architecture
     Search         Lookup         Lookup
    (Qdrant)     (PostgreSQL)      (Tools)
          │           │            │
          └───────────┼────────────┘
                      ▼
            Context Validation
                      │
          Enough? ────┤──── No
             │        ▼
             │   Retrieve More
             ▼
        Tool Execution
             │
             ▼
   Generate Answer / Patch
             │
             ▼
      Grounding Check
             │
             ▼
          Final Response