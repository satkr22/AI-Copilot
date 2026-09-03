# AI Copilot Project Progress

Last updated: 2026-09-04

## Current Status

The project has completed the foundation, repository lifecycle, and repository materialization phases. The application is currently a working FastAPI + React + PostgreSQL + Qdrant setup with user-owned projects, local repository snapshots, GitHub clone import, ZIP upload/extraction, and branch-level commit tracking.

The current implementation is intentionally still pre-indexing. There is no Tree-sitter parsing, symbol extraction, chunking, embeddings, Qdrant search logic, LangGraph workflow, or repository chat yet.

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
      -> File discovery service
      -> Indexing service skeleton
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
- Create and attach a GitHub repository snapshot record.

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
POST /projects/{project_id}/repository/zip
DELETE /projects/{project_id}/repository
DELETE /projects/{project_id}
```

## Day 3 Completed: Repository Lifecycle And Storage Foundation

Implemented:

- Local repository storage service.
- Storage path generation per user and repository.
- Safe repository storage directory creation.
- Safe repository storage deletion.
- GitHub repository records now get a local storage path.
- ZIP repository upload endpoint.
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

Day 3 created the repository lifecycle and storage foundation. Day 4 later added actual clone/extraction materialization on top of this storage layer.

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
- Display branch names and short commit hashes for attached repositories.
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
- GitHub clone materialization
- ZIP extraction/materialization
- Branch-level repository snapshot metadata
- File discovery utility prepared for indexing

Not included yet:

- Indexing job persistence.
- Repository file metadata persistence.
- Tree-sitter parsing.
- Symbol extraction.
- Import extraction.
- Function call extraction.
- API endpoint extraction.
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
- repository_branches
- future indexing_jobs
- future repository_files
- future symbols
- future chunks
- future chat metadata

Qdrant will only store vector embeddings and small payload metadata.

### Local Storage First

Repository files are stored locally in V1.

Reason:

```text
Local storage keeps development simple. S3 can be added later if deployment requirements justify it.
```

## Day 4 Completed: Repository Materialization And Branch Snapshot Foundation

Date: 2026-09-04

Day 4 moved the project from repository metadata only into real repository materialization on local storage.

Implemented:

- GitHub repository import now attempts to clone the repository into the local repository storage folder.
- Backend Docker image now installs `git`, allowing the backend container to perform GitHub clone operations.
- ZIP repository upload now stores the uploaded archive using a constant filename, extracts it into the repository storage folder, and removes the uploaded ZIP after successful extraction.
- ZIP extraction includes path traversal protection to prevent archive entries from escaping the repository storage folder.
- Repository storage cleanup still removes local repository folders when orphan repositories are deleted.
- A new `repository_branches` table/model was added to support the revised branch-level indexing design.
- `RepositoryBranch` is now imported through `backend/app/models/__init__.py`, so database table creation can discover the model directly.
- GitHub import identifies remote branches and stores each branch name with its latest commit hash in `repository_branches`.
- `repositories` now represents repository-level metadata, while branch commit tracking belongs to `repository_branches`.
- ZIP uploads without `.git` are initialized as Git repositories with an initial `main` commit.
- ZIP uploads containing `.git` are validated as existing Git repositories.
- Repository validation checks Git structure, object integrity, and unsafe symlinks.
- Existing repository attach duplicates the source repository into a new repository snapshot and stores fresh branch rows.
- Repository API responses include branch snapshot data.
- Minimal frontend display shows branch names and short commit hashes.
- Import exception handling preserves real `HTTPException` responses such as `404 Project not found`.
- Expected GitHub/ZIP import failures return clean `406` responses.
- Failed GitHub/ZIP imports delete partial local storage and roll back pending DB state.
- A `FileDiscoveryService` was added with Git commit-based discovery, ignored directory filtering, and max file size filtering.

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
Repository API branch response: implemented
Minimal frontend branch display: implemented
Import exception handling: implemented
File discovery foundation: created intentionally for Day 5 indexing
```

Important Day 4 boundary:

```text
FileDiscoveryService exists, but it is intentionally not wired into repository ingestion.
File discovery is the first step of Day 5 indexing.
```

## Next Phase: Day 5 Indexing Foundation

Day 5 should start the indexing pipeline, not the AI chat workflow.

Primary goal:

```text
Repository snapshot exists locally
-> create indexing job
-> discover files from branch commit snapshots
-> persist repository file metadata
-> update indexing status/timestamps
-> prepare for Tree-sitter parsing and chunking later
```

Day 5 should implement:

- `indexing_jobs` model/table.
- `repository_files` model/table.
- Indexing service flow using existing `FileDiscoveryService`.
- Minimal indexing trigger API.
- Indexing success/failure state persistence.
- Branch and repository `indexed_at` timestamp updates after successful discovery.

Day 5 should not implement yet:

- Tree-sitter parsing.
- Symbol extraction.
- Chunking.
- Embeddings.
- Qdrant writes.
- LangGraph workflow.
- Repository chat.