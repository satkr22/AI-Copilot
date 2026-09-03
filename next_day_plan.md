# Next Day Plan: Day 5 Indexing Foundation

## Goal

Build the first real indexing layer on top of completed repository snapshots.

Day 5 should not add LangGraph, chat, embeddings, or Qdrant writes yet. It should create a reliable indexing foundation that discovers files from stored branch commit snapshots and persists structured metadata in PostgreSQL.

## Scope

Implement:

- Indexing job model/table.
- Repository file model/table.
- Indexing service flow that starts from a repository and its `repository_branches`.
- File discovery using existing `FileDiscoveryService`.
- File metadata persistence.
- Basic indexing status fields and timestamps.
- Minimal API endpoint to trigger indexing for a repository or project repository.

Do not implement yet:

- Tree-sitter parsing.
- Symbol extraction.
- Import extraction.
- Chunking.
- Embeddings.
- Qdrant vector writes.
- LangGraph workflow.
- Repository chat.

## Proposed Data Model

Add `indexing_jobs`:

- `id`
- `repository_id`
- `status`: `pending`, `running`, `completed`, `failed`
- `started_at`
- `completed_at`
- `error_message`
- `created_at`

Add `repository_files`:

- `id`
- `repository_id`
- `repository_branch_id`
- `path`
- `commit_hash`
- `size_bytes`
- `language`
- `indexed_at`
- `created_at`

Use `repository_branch_id` so indexing remains branch-snapshot aware.

## Service Flow

Create or complete the indexing flow in `IndexingService`:

```text
index_repository(repository)
-> create indexing job
-> mark job running
-> load repository branches
-> for each branch:
     -> call FileDiscoveryService.discover(repository_root, branch_name, latest_commit_hash)
     -> persist one repository_files row per discovered file
     -> update branch.indexed_at
-> update repository.indexed_at
-> mark job completed
```

Failure behavior:

- Mark job as `failed`.
- Store a short error message.
- Do not delete repository storage.
- Do not remove existing repository or branch rows.

## API

Add one minimal trigger endpoint:

```text
POST /repositories/{repository_id}/index
```

Behavior:

- Require current user ownership.
- Return the created/completed indexing job.
- For now, synchronous execution is acceptable.
- Background workers can be added later if indexing becomes slow.

Optional project-scoped convenience endpoint, only if useful:

```text
POST /projects/{project_id}/repository/index
```

If added, it should just resolve the attached repository and call the same service.

## File Discovery Rules

Use the existing `FileDiscoveryService` as the first indexing step.

Keep the current rules:

- Use `git ls-tree` against the stored branch commit hash.
- Skip `.git`, `node_modules`, build outputs, virtualenv folders, and cache folders.
- Skip `.env`.
- Skip files above the configured max size.
- Read contents later from the exact commit using `git show`.

For Day 5, persist metadata first. Reading full file contents can be introduced when parsing/chunking begins.

## Verification

Run:

```bash
python -m compileall backend/app
```

Recommended manual checks:

- Import a GitHub repository, then trigger indexing.
- Upload a ZIP repository without `.git`, then trigger indexing.
- Upload a ZIP repository with `.git`, then trigger indexing.
- Confirm `indexing_jobs` records success/failure.
- Confirm `repository_files` rows are linked to repository and branch rows.
- Confirm repeated indexing does not create uncontrolled duplicate file rows.

## Acceptance Criteria

Day 5 is complete when:

- A materialized repository can be indexed through an API call.
- Each branch snapshot can produce discovered file metadata.
- Indexing status is persisted.
- Repository and branch `indexed_at` timestamps are updated on success.
- Failed indexing records the failure without damaging repository storage.
