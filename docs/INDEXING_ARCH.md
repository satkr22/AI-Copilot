# Indexing Architecture Flow

```plaintext
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
        Repository Snapshot
            ↓

        Discover Files

            ↓

        Detect Language

            ↓

        Select Provider

            ↓

        Extract Symbols

            ↓

        Extract Imports

            ↓

        Generate Chunks

            ↓

        Persist Symbols

            ↓

        Persist Imports

            ↓

        Persist Chunks

            ↓

        Update Job Status