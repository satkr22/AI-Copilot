Repository DB
    ↓
local_path
    ↓
Local Git repository
    ↑
    │
RepositoryBranch DB
    ├── branch_name
    └── latest_commit_hash
             ↓
      IndexingService
             ↓
    FileDiscoveryService
             ↓
       exact Git tree
             ↓
       file contents
             ↓
      parsing/chunking
             ↓
       embeddings
             ↓
        Redis/vector DB