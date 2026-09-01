# Day 5 Plan: File Discovery And Branch-Aware Repository Metadata

## Goal

Turn Day 4 materialized repositories into structured file metadata that can be used by the future indexing pipeline.

Day 5 should not add Tree-sitter parsing, embeddings, Qdrant writes, LangGraph, or repository chat yet. The focus is to create a clean backend foundation for discovering source files and saving enough metadata for Day 6 indexing jobs.

## Main Outcomes

- Add persistent discovered-file metadata.
- Connect file discovery to ZIP and GitHub ingestion.
- Make GitHub discovery compatible with the new `repository_branches` model.
- Keep routes thin and keep repository lifecycle behavior working.
- Update response schemas and frontend display so repository branches are visible instead of old repository-level `branch` and `commit_hash` fields.

## Backend Changes

Add a `repository_files` model/table.

Suggested fields:

```text
id
repository_id
repository_branch_id nullable
path
language nullable
size_bytes
content_hash nullable
created_at
```

Rules:

- ZIP files use `repository_id` and `repository_branch_id = null`.
- GitHub files should be linked to the matching `repository_branch_id`.
- Store relative paths only, never absolute local paths.
- Keep file content out of PostgreSQL.

Extend `FileDiscoveryService`.

Required behavior:

- Discover regular files under a materialized repository folder.
- Skip `.git`, `node_modules`, `__pycache__`, `dist`, `build`, `.next`, `.venv`, `venv`, and environment/cache folders.
- Skip files larger than the current max file size limit.
- Return metadata with relative path, size, simple language detection, and optional content hash.
- Add a save method that replaces previous discovered file rows for the same repository or branch before inserting fresh results.

GitHub branch behavior:

```text
For Day 5, prefer branch-aware discovery using git ls-tree.
For each RepositoryBranch:
  read the branch tree from origin/{branch_name}
  save file paths linked to that repository_branch_id
```

This avoids repeatedly checking out branches and keeps the local clone stable.

ZIP behavior:

```text
After ZIP extraction:
  discover files from the extracted folder
  save rows with repository_branch_id = null
```

## API And Frontend Changes

Backend responses:

- Add a branch response schema for `RepositoryBranch`.
- Include `branches` in `RepositoryResponse` for GitHub repositories.
- Keep repository-level response fields focused on repository metadata: id, source type, source URL, local path, created time, indexed time.

Frontend:

- Remove old assumptions that every repository has repository-level `branch` and `commit_hash`.
- Show GitHub repository branches as a small list in the project detail view.
- For ZIP repositories, show that the repository has no branches.
- Keep the UI minimal; this is still a backend workflow validation screen.

## Cleanup And Fixes

- Fix route exception handling so existing `HTTPException` values pass through unchanged.
- Only convert real clone/extract failures into import-specific errors.
- Remove duplicate imports in repository services.
- Remove debug `print()` calls from storage cleanup and route handlers.
- Clean spelling in comments where it affects readability.
- Keep `RepositoryBranch` imported through `backend/app/models/__init__.py`.

## Verification

Run:

```text
python -m compileall backend/app
npm run build
docker compose build backend
docker compose up
```

Manual checks:

- Register or login.
- Create a project.
- Upload a valid ZIP and confirm discovered file rows are created.
- Upload an unsafe ZIP and confirm it is rejected without leaving repository storage or database rows in a bad state.
- Import a public GitHub repository and confirm branch rows plus branch file rows are created.
- Detach an orphan repository and confirm repository, branches, files, and local storage are cleaned up.
- Delete a project with an orphan repository and confirm the same cleanup behavior.

## Day 5 Completion Criteria

Day 5 is complete when:

- Materialized ZIP repositories produce saved file metadata.
- Materialized GitHub repositories produce saved branch-aware file metadata.
- Repository API responses expose branch information consistently.
- Frontend no longer expects `branch` or `commit_hash` directly on repository rows.
- Existing project/repository lifecycle flows still work.
