# AI Software Engineer Copilot MVP

## Product Goal

Build a repository-aware AI engineering assistant that helps developers understand, search, explain, and reason about codebases using repository intelligence, RAG, LangGraph, and controlled tool use.

The MVP should demonstrate strong backend engineering and AI engineering without becoming a Cursor or Devin clone.

## Positioning

This project is:

```text
A production-style repository intelligence and agentic RAG system for software engineering tasks.
```

It is not:

```text
An autonomous coding agent.
A full IDE replacement.
A multi-agent Devin clone.
An enterprise platform with unnecessary infrastructure.
```

## V1 Principles

- Build depth over feature count.
- Use a modular monolith.
- Keep the project realistic for one developer.
- Include LangGraph in V1, but as one focused workflow.
- Use PostgreSQL for structured metadata.
- Use Qdrant for semantic vector search.
- Use local filesystem storage for repository snapshots.
- Treat repositories as snapshots, not live synchronized GitHub mirrors.
- Return code suggestions as proposed patches only.
- Avoid automatic code modification in V1.

## V1 Tech Stack

Backend:

- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL

AI:

- LangGraph
- LangChain
- Tree-sitter
- Qdrant
- One LLM provider

Frontend:

- React
- TypeScript
- Vite

Infrastructure:

- Docker Compose
- Local filesystem repository storage

Future deployment target:

- Single EC2 instance running Docker Compose

## Explicitly Excluded From V1

- Kubernetes
- Kafka
- RabbitMQ
- Redis
- Neo4j
- Microservices
- Multiple LLM providers
- Private GitHub OAuth
- External MCP servers
- IDE extension
- Terminal execution by the agent
- Automatic PR creation
- Long-running autonomous coding loops
- Large multi-agent system

## Core User Flow

```text
User registers/logs in
-> creates a project
-> attaches a repository snapshot through ZIP or GitHub URL
-> system stores repository locally
-> system indexes files
-> system extracts repository intelligence
-> user asks repository-aware questions
-> LangGraph workflow plans, retrieves, uses tools, validates context, if required retrieves more and answers with citations
```

## Repository Ownership Model

```text
User -> many Projects
User -> many Repositories
Repository -> many Projects
Project -> zero or one Repository
```

Meaning:

- A project can be created without a repository.
- A project can later attach one repository.
- A repository snapshot can be reused across multiple projects owned by the same user.
- Repository deletion happens only when the repository becomes orphaned.

## Repository Snapshot Model

In V1, repositories are snapshots.

For GitHub:

```text
Store source URL
Store branch
Clone current repository state
Store commit hash
Index that fixed snapshot
```

For ZIP:

```text
Upload ZIP
Store ZIP/source files locally
Extract into repository storage
Index that fixed snapshot
```

Live synchronization is V2.

## Backend Architecture

```text
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
      retrieval/
      intelligence/
      architecture/
      chat/
      codegen/
    ai/
      graphs/
      prompts/
      tools/
      mcp/
    main.py
```

Backend responsibilities:

- Request validation.
- Authentication boundary.
- Project and repository lifecycle.
- Repository storage.
- Indexing orchestration.
- Database persistence.
- Retrieval APIs.
- AI workflow invocation.

Routes should stay thin. Business logic belongs in services.

## AI Integration Architecture

```text
backend/app/ai/
  graphs/
    repository_agent_graph.py
    state.py
    nodes.py
  prompts/
    intent_classifier.py
    answer_generation.py
    grounding_check.py
    code_suggestion.py
  tools/
    repo_tools.py
  mcp/
    local_repo_mcp.py
  evaluators/
    grounding_evaluator.py
```

AI responsibilities:

- Classify engineering intent.
- Plan required repository context.
- Retrieve semantic and structured context.
- Select tools.
- Read exact repository files/symbols when needed.
- Validate whether enough evidence exists.
- Generate answer or patch.
- Check grounding and citations.

## LangGraph V1 Workflow

Use one intelligent workflow:

```text
classify_intent
-> plan_context
-> retrieve_initial_context
-> context_validation
-> retrieve_more if needed
-> tool_selection
-> tool_execution
-> generate_answer_or_patch
-> grounding_check
-> final_response
```

This is agentic because the system makes decisions about intent, context, retrieval, tools, sufficiency, and grounding.

It avoids fake complexity by not creating many specialized agents.

## MCP-Style Local Tools

V1 should implement a local repository tool layer:

```text
repo.list_files(project_id, path_prefix?)
repo.read_file(project_id, path, start_line?, end_line?)
repo.search_symbols(project_id, query, kind?)
repo.semantic_search(project_id, query, top_k)
repo.get_file_summary(project_id, path)
repo.get_module_summary(project_id, module_path)
repo.get_architecture_summary(project_id)
```

These are MCP-style tools because they expose controlled repository operations through stable tool interfaces. A real MCP server can be added later without rewriting the repository intelligence layer.

## Repository Indexing Pipeline

```text
Repository snapshot exists locally
-> create indexing job
-> discover files
-> apply ignore rules
-> detect language
-> parse supported files with Tree-sitter
-> extract symbols
-> extract imports
-> extract API endpoints where feasible
-> extract lightweight function calls where feasible
-> create chunks
-> store metadata in PostgreSQL
-> create embeddings
-> store vectors in Qdrant
-> update indexing job status
```

Supported languages for V1:

- Python
- JavaScript
- TypeScript
- C
- C++
- JAVA

Best-effort metadata:

- files
- symbols
- imports
- API routes
- function calls
- file summaries
- module summaries
- repository statistics
- architecture summary

## Retrieval Pipeline

```text
User query
-> classify intent
-> create retrieval plan
-> semantic search in Qdrant
-> structured lookup in PostgreSQL
-> optional keyword/path/symbol search
-> merge and deduplicate results
-> validate context sufficiency
-> fetch more context if needed
-> send cited context to LLM
```

Every result should preserve:

- file path
- line range
- symbol name when available
- source type
- relevance reason

## Database Scope

Implemented or in progress:

- users
- projects
- repositories

Planned V1 tables:

- indexing_jobs
- files
- symbols
- imports
- function_calls
- api_endpoints
- chunks
- modules
- module_dependencies
- repo_statistics
- architecture_summaries
- chat_sessions
- chat_messages
- code_suggestions

PostgreSQL stores actual chunk text and metadata. Qdrant stores embeddings with small payloads that point back to PostgreSQL records.

## API Scope

Current foundation APIs:

```text
POST   /auth/register
POST   /auth/login
GET    /auth/me

POST   /projects
GET    /projects
GET    /projects/{project_id}
DELETE /projects/{project_id}

GET    /repositories
GET    /repositories/{repository_id}

GET    /projects/{project_id}/repository
PUT    /projects/{project_id}/repository
POST   /projects/{project_id}/repository/github
POST   /projects/{project_id}/repository/zip
DELETE /projects/{project_id}/repository
```

Planned indexing APIs:

```text
POST /projects/{project_id}/index
GET  /projects/{project_id}/indexing-jobs/latest
```

Planned repository intelligence APIs:

```text
GET  /projects/{project_id}/files
GET  /projects/{project_id}/files/{file_id}
GET  /projects/{project_id}/symbols
GET  /projects/{project_id}/modules
GET  /projects/{project_id}/statistics
```

Planned AI APIs:

```text
POST /projects/{project_id}/search
POST /projects/{project_id}/chat
POST /projects/{project_id}/explain
GET  /projects/{project_id}/architecture
POST /projects/{project_id}/code/suggest
```

## Frontend Scope

V1 frontend should include:

- login/register screen
- project dashboard
- create project form
- project detail page
- repository attach/detach controls
- ZIP upload
- indexing status view
- repository explorer
- search page
- chat page with citations
- architecture overview page

The frontend should remain simple until repository intelligence works.

## V1 Success Criteria

The MVP is successful when a user can:

1. Create a project.
2. Attach a GitHub or ZIP repository snapshot.
3. Index the repository.
4. Browse discovered files and symbols.
5. Search repository content semantically.
6. Ask repository-aware questions.
7. Receive grounded answers with citations.
8. View an architecture overview.
9. Generate a proposed code patch without automatic file modification.

## Development Roadmap

Completed:

- Day 1: application foundation.
- Day 2: user/project/repository foundation.
- Day 3: repository lifecycle and storage foundation.

Next:

- Day 4: repository materialization and file discovery.
- Day 5: indexing job model and indexing status API.
- Day 6: Tree-sitter parser foundation.
- Day 7: symbol/import extraction.
- Day 8: chunking and metadata persistence.
- Day 9: embeddings and Qdrant indexing.
- Day 10: semantic search API.
- Day 11: LangGraph workflow skeleton.
- Day 12: repository tools and grounding.
- Day 13: repository chat.
- Day 14: architecture overview.

## V2 Scope

Add only after V1 is complete:

- private GitHub OAuth
- live repository sync
- PR review
- external MCP integrations
- controlled patch application
- test generation
- Redis queue
- S3 storage
- Neo4j if graph traversal becomes central
- IDE extension
- multi-agent workflows for clearly separate tasks

