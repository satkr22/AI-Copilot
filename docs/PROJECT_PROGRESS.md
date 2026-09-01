# AI Copilot Project Progress

Last updated: 2026-08-31

## Current Status

The project has completed the foundation phase and the initial repository lifecycle phase. The application is currently a working FastAPI + React + PostgreSQL + Qdrant setup with user-owned projects and repository snapshots.

The current implementation is intentionally still pre-indexing. There is no LangGraph, RAG, Tree-sitter, embeddings, or Qdrant search logic yet.

## Implemented Architecture

```text
React Frontend
  -> FastAPI Backend
      -> Auth/User routes
      -> Project routes
      -> Repository routes
      -> Project service
      -> Repository service
      -> Storage service
      -> SQLAlchemy models
  -> PostgreSQL
  -> Qdrant
  -> Local filesystem storage
```

## Day 1 Completed: Project Foundation

Implemented:

- Docker Compose setup.
- FastAPI backend container.
- React/Vite frontend container.
- PostgreSQL container.
- Qdrant container.
- Backend health endpoint.
- CORS configuration for frontend-to-backend communication.
- Environment-based configuration with Pydantic settings.
- Basic frontend-backend compatibility.

Key files:

- `docker-compose.yml`
- `backend/Dockerfile`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `frontend/src/App.tsx`

Outcome:

- All four services run through Docker Compose.
- Backend and frontend can communicate.
- The project has a real app foundation instead of isolated experiments.

## Day 2 Completed: User, Project, And Repository Foundation

Implemented:

- User registration.
- User login.
- Simple bearer-token auth using the user id.
- Current user endpoint.
- Project creation.
- Project listing.
- Project detail fetch.
- Repository listing.
- Repository detail fetch.
- Attach existing repository to a project.
- Create a GitHub repository snapshot record and attach it to a project.

Current relationship model:

```text
User -> many Projects
User -> many Repositories
Repository -> many Projects
Project -> zero or one Repository
```

Important rule:

```text
A project can be created without a repository.
A repository is attached later.
A repository snapshot can be reused by multiple projects of the same user.
```

Implemented API surface:

```text
POST /auth/register
POST /auth/login
GET  /auth/me

POST /projects
GET  /projects
GET  /projects/{project_id}

GET  /repositories
GET  /repositories/{repository_id}

GET  /projects/{project_id}/repository
PUT  /projects/{project_id}/repository
POST /projects/{project_id}/repository/github
```

## Day 3 Completed: Repository Lifecycle And Storage Foundation

Implemented:

- Local repository storage service.
- Storage path generation per user and repository.
- Safe repository storage directory creation.
- Safe repository storage deletion.
- GitHub repository records now get a local storage path.
- ZIP repository upload endpoint.
- ZIP file saving into local repository storage.
- Detach repository from project.
- Delete project.
- Orphan repository cleanup.

Repository storage layout:

```text
storage/repositories/{user_id}/{repository_id}/
```

Implemented lifecycle APIs:

```text
POST   /projects/{project_id}/repository/zip
DELETE /projects/{project_id}/repository
DELETE /projects/{project_id}
```

Orphan cleanup rule:

```text
When a repository is detached from a project, delete the repository row and local storage only if no other project owned by the user references it.

When a project is deleted, delete its attached repository row and local storage only if no other project owned by the user references it.
```

Current ZIP behavior:

```text
ZIP file is accepted and stored.
ZIP is not extracted yet.
Repository files are not indexed yet.
```

Current GitHub behavior:

```text
GitHub URL and branch are stored.
Local storage folder is created.
Repository is not cloned yet.
Commit hash is not captured yet.
```

## Frontend Current Behavior

Implemented:

- Register/login page.
- Dashboard after login.
- Create project from dashboard.
- List projects on dashboard.
- Click project to open project detail page.
- Project detail shows attached repository if present.
- Project detail shows repository attach options if no repository is attached.
- Attach repository through GitHub URL.
- Attach an existing repository.
- Upload ZIP repository.
- Detach repository from project.
- Delete project.

Frontend is intentionally minimal. It exists to test the backend workflow and demonstrate the product flow.

## Current Technical Boundaries

Included so far:

- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- Qdrant container
- React/Vite
- Docker Compose
- Local filesystem storage

Not included yet:

- Actual GitHub clone.
- ZIP extraction.
- Indexing jobs.
- File discovery.
- Tree-sitter parsing.
- Symbol extraction.
- Chunking.
- Embeddings.
- Qdrant vector writes.
- Semantic search.
- LangGraph workflow.
- MCP-style repository tools.
- Repository chat.
- Architecture analysis.

## Current Design Decisions

### Modular Monolith

The backend is a modular monolith. Routes, schemas, models, services, storage, and future AI logic live in one FastAPI application with clear internal boundaries.

Reason:

```text
This keeps the MVP buildable by one developer while still showing production-style backend architecture.
```

### Repository Snapshots

Repositories are treated as snapshots in V1.

Reason:

```text
AI answers should be grounded against a known repository state. Live GitHub sync is useful but belongs in V2.
```

### PostgreSQL As Source Of Truth

PostgreSQL owns structured data:

- users
- projects
- repositories
- future files
- future symbols
- future chunks
- future indexing jobs

Qdrant will only store vector embeddings and small payload metadata.

### Local Storage First

Repository files are stored locally in V1.

Reason:

```text
Local storage keeps development simple. S3 can be added later if deployment requirements justify it.
```

## Known Gaps To Address Soon

- Add ZIP extraction.
- Add GitHub clone.
- Add commit hash capture for GitHub snapshots.
- Add indexing job model and API.
- Add file discovery and ignore rules.
- Clean generated `__pycache__` files from the working tree if they are not ignored correctly.
- Avoid expanding auth complexity further until core repository intelligence is working.

## Next Phase

Day 4 should focus on turning repository snapshots into real local source trees:

```text
ZIP extraction
GitHub clone
repository snapshot validation
file discovery foundation
ignore rules
```


## Day 4 Progress Update: Repository Materialization And Branch Snapshot Foundation

Date: 2026-09-02

Day 4 moved the project from repository metadata only toward real repository materialization on local storage.

Implemented or started:

- GitHub repository import now attempts to clone the repository into the local repository storage folder.
- Backend Docker image now installs `git`, allowing the backend container to perform GitHub clone operations.
- ZIP repository upload now stores the uploaded archive using a constant filename, extracts it into the repository storage folder, and removes the uploaded ZIP after successful extraction.
- ZIP extraction includes path traversal protection to prevent archive entries from escaping the repository storage folder.
- Repository storage cleanup still removes local repository folders when orphan repositories are deleted.
- A new `repository_branches` table/model was added to support the revised branch-level indexing design.
- `RepositoryBranch` is now imported through `backend/app/models/__init__.py`, so database table creation can discover the model directly.
- GitHub import identifies remote branches and stores each branch name with its latest commit hash in `repository_branches`.
- `repositories` now represents repository-level metadata, while branch commit tracking belongs to `repository_branches`.
- A `FileDiscoveryService` was added with basic directory walking, ignored directory filtering, and max file size filtering.

Updated repository snapshot decision:

```text
Clone the repository once.
Identify repository branches.
Store each branch's latest commit hash in repository_branches.
Later indexing will process each branch and maintain indexed_at per branch.
```

Current Day 4 status:

```text
ZIP extraction: implemented
GitHub clone: implemented
Repository branch discovery: implemented
Branch commit hash storage: implemented in repository_branches
RepositoryBranch model registration: fixed
File discovery foundation: created but not wired into ingestion yet
Exception handling cleanup: still pending
```

What still needs to be added or fixed from Day 4:

- Wire `FileDiscoveryService` into the ingestion flow after ZIP extraction and after GitHub clone/branch discovery.
- Decide and add persistence for discovered files, most likely a future `repository_files` table linked to `repositories` and optionally `repository_branches`.
- For GitHub repositories, decide whether Day 5 file discovery should inspect only the checked-out tree first or use `git ls-tree` for each remote branch.
- Update API response schemas and frontend display to match the new branch-level model instead of expecting `branch` and `commit_hash` directly on `repositories`.
- Improve route exception handling so existing `HTTPException` errors such as project not found are not masked as clone or ZIP failures.
- Clean up duplicate imports, debug `print()` calls, spelling issues in comments, and formatting in repository services.
- Add focused tests or manual verification notes for GitHub clone success, clone failure cleanup, ZIP extraction success, unsafe ZIP rejection, and orphan cleanup after materialized repositories.




# My comments:
- Clone the repository once, identify the branches, process each branch's current tree, and maintain the index at the latest successfully indexed commit for each branch.

- fix exception handlingm properly to solve masking problem.

- add: if zip repo is git repo then find its branches and save save each brach name and commit in 'repository_branch' table. other wise simply make it git repo and then follow the same as for u did for git repo storage.