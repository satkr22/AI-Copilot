# AI Copilot

Repository-aware AI Copilot MVP.

The project is a backend-heavy FastAPI + React system for importing repository snapshots, preparing them for indexing, and later powering repository-aware retrieval and AI workflows. The MVP intentionally stays focused: no autonomous coding loops, no IDE clone, no multi-agent system, and no enterprise infrastructure.

## Current Status

Completed:

- Docker Compose foundation for backend, frontend, PostgreSQL, and Qdrant.
- User registration, login, and current-user endpoint.
- Project creation, listing, detail, deletion, and project-scoped repository actions.
- Repository ownership model:

```text
User -> many Projects
User -> many Repositories
Repository -> many Projects
Project -> zero or one Repository
```

- Local repository storage under:

```text
storage/repositories/{user_id}/{repository_id}/
```

- GitHub repository import into local storage.
- ZIP repository upload, safe extraction, and Git initialization when uploaded source is not already a Git repository.
- Branch-level snapshot tracking through `repository_branches`.
- Minimal frontend flow for login, project creation, repository attach/import/upload, detach, and delete.

Still not started:

- Real indexing jobs.
- Repository file metadata persistence.
- Tree-sitter parsing.
- Symbol/import/API extraction.
- Chunking.
- Embeddings.
- Qdrant writes/search.
- LangGraph repository chat workflow.

## Day 4 Completed: Repository Materialization

Day 4 moved the app from repository metadata into real local repository snapshots.

Implemented:

- GitHub imports clone public repositories into local repository storage.
- ZIP uploads are extracted safely with path traversal protection.
- ZIP uploads without `.git` are converted into Git repositories with an initial `main` commit.
- ZIP uploads containing `.git` are validated as Git repositories.
- Repository validation checks Git structure, object integrity, and unsafe symlinks.
- Branch names and commit hashes are captured in `repository_branches`.
- Repository API responses include branch snapshot data.
- Import route errors preserve real `HTTPException` responses, so missing projects still return `404`.
- Expected import failures return clean `406` responses.
- Failed GitHub/ZIP imports clean local storage and roll back pending DB state.

Important boundary:

```text
FileDiscoveryService exists, but it is intentionally not wired into repository ingestion.
It is the first step of Day 5 indexing.
```

## Next Phase: Day 5 Indexing Foundation

Day 5 should start the indexing pipeline without adding AI chat yet.

Primary goal:

```text
Repository snapshot exists locally
-> create indexing job
-> discover files from branch commit snapshots
-> persist file metadata
-> prepare for parsing/chunking in later steps
```

Start with `next_day_plan.md`.
