# AI Software Engineer Copilot --- Detailed System Architecture 

> This document describes the production-grade architecture for the AI
> Software Engineer Copilot MVP.

------------------------------------------------------------------------

# 1. High-Level System Architecture

``` text
                   +-------------------------+
                   |      React Frontend     |
                   |-------------------------|
                   | Dashboard               |
                   | Repository Chat         |
                   | Search                  |
                   | Architecture Viewer     |
                   | Flow Viewer             |
                   | Code Generation         |
                   | Documentation           |
                   +-----------+-------------+
                               |
                         REST / WebSocket
                               |
                +--------------v---------------+
                |        FastAPI Backend       |
                |------------------------------|
                | Authentication               |
                | Projects API                 |
                | Repository API               |
                | Chat API                     |
                | Agent API                    |
                | Code Generation API          |
                | Search API                   |
                +--------------+---------------+
                               |
 ------------------------------------------------------------
 |            |             |             |                 |
 v            v             v             v                 v
Repository   AI Engine   Background    MCP Server     Storage Layer
 Service    (LangGraph)    Workers
```

------------------------------------------------------------------------

# 2. Frontend Layer

    Frontend
    ├── Login
    ├── Dashboard
    ├── Projects
    ├── Repository Viewer
    ├── Search
    ├── AI Chat
    ├── Code Generation
    ├── Documentation
    ├── Architecture Graph
    ├── Dependency Graph
    ├── Flow Viewer
    ├── Settings
    └── Agent Execution Monitor

The Agent Execution Monitor visualizes each LangGraph execution step:

    Planning...
    Searching Repository...
    Finding Symbols...
    Retrieving Context...
    Generating Code...
    Validating...
    Done

------------------------------------------------------------------------

# 3. API Layer (FastAPI)

    FastAPI
    ├── Auth API
    ├── User API
    ├── Project API
    ├── Repository API
    ├── Chat API
    ├── Search API
    ├── Generation API
    ├── Documentation API
    ├── Architecture API
    ├── Debug API
    ├── Agent API
    └── WebSocket

Responsibilities: - Authentication & Authorization - Request
Validation - API Routing - Calling Services - Streaming Responses

No business logic should live here.

------------------------------------------------------------------------

# 4. Repository Intelligence Pipeline

    Repository Uploaded
            ↓
    Clone Repository
            ↓
    Language Detection
            ↓
    Tree-sitter Parsing
            ↓
    AST Generation
            ↓
    Symbol Extraction
            ↓
    Import & Dependency Analysis
            ↓
    API Discovery
            ↓
    Database Model Discovery
            ↓
    Documentation Extraction
            ↓
    Chunking
            ↓
    Embedding Generation
            ↓
    Knowledge Graph Creation
            ↓
    Vector Database Indexing

Output:

-   Files
-   AST
-   Classes
-   Interfaces
-   Functions
-   Methods
-   Variables
-   APIs
-   Routes
-   DTOs
-   Models
-   Services
-   Controllers
-   Imports
-   Dependencies
-   Call Graph
-   Module Graph
-   Embeddings
-   Metadata

------------------------------------------------------------------------

# 5. Repository Knowledge Layer

    Knowledge Service
    ├── File Index
    ├── Symbol Index
    ├── AST Index
    ├── Vector Search
    ├── BM25 Search
    ├── Hybrid Search
    ├── Dependency Graph
    ├── Call Graph
    ├── Metadata Store
    └── Cache

Hybrid Retrieval Flow:

    User Query
          ↓
    Vector Search
          +
    BM25 Search
          +
    Graph Search
          +
    AST Search
          ↓
    Merge Results
          ↓
    LLM

------------------------------------------------------------------------

# 6. Storage Layer

## PostgreSQL

-   Users
-   Projects
-   Repositories
-   Chat History
-   Logs
-   Settings

## Qdrant

-   Embeddings
-   Semantic Search

## Neo4j

-   Dependency Graph
-   Call Graph
-   Architecture Graph
-   Module Relationships

## Redis

-   Cache
-   Sessions
-   Job Status

## MinIO / S3

-   Repository ZIPs
-   Generated Documentation
-   Logs

------------------------------------------------------------------------

# 7. LangGraph Workflow Engine

    Request
       ↓
    Planner
       ↓
    Intent Detection
       ↓
    Task Decomposition
       ↓
    Parallel Specialized Agents
       ↓
    Aggregation
       ↓
    Verification
       ↓
    Final Response

Example:

    User: Add JWT Authentication

    Planner
       ↓
    Repository Agent
       ↓
    Retriever
       ↓
    Architecture Agent
       ↓
    Code Generation Agent
       ↓
    Validation Agent
       ↓
    Final Response

------------------------------------------------------------------------

# 8. Specialized Agents

-   Planner Agent
-   Repository Agent
-   Retriever Agent
-   Architecture Agent
-   Code Generation Agent
-   Documentation Agent
-   Testing Agent
-   Debug Agent
-   Validation Agent

------------------------------------------------------------------------

# 9. MCP Layer

Current Integrations

-   GitHub
-   Filesystem
-   Terminal
-   Documentation

Future Integrations

-   Jira
-   Slack
-   Docker
-   Kubernetes
-   PostgreSQL
-   Redis
-   Cloud Providers

------------------------------------------------------------------------

# 10. Background Workers

    Clone Repository
          ↓
    AST Parsing
          ↓
    Embedding Generation
          ↓
    Knowledge Graph
          ↓
    Documentation
          ↓
    Architecture Graph

Runs asynchronously.

------------------------------------------------------------------------

# 11. LLM Abstraction Layer

-   OpenAI
-   Anthropic
-   Gemini
-   Local Models

Provides routing logic and keeps the application model-agnostic.

------------------------------------------------------------------------

# 12. End-to-End Request Flow

    User
          ↓
    React Frontend
          ↓
    FastAPI
          ↓
    LangGraph Planner
          ↓
    Intent Classification
          ↓
    Repository Agent
          ↓
    Knowledge Layer
    (Vector + BM25 + Graph + AST)
          ↓
    Architecture Agent
          ↓
    Code Generation Agent
          ↓
    Validation Agent
          ↓
    Response Aggregator
          ↓
    FastAPI
          ↓
    Frontend

------------------------------------------------------------------------

# 13. Architectural Improvements

-   Separate Repository Intelligence Pipeline from the Knowledge Layer.
-   Hybrid Retrieval (Vector + BM25 + AST + Graph).
-   Neo4j for dependency and architecture reasoning.
-   Dedicated Validation Agent.
-   LLM abstraction layer.
-   LangGraph orchestration backbone.
-   Asynchronous indexing pipeline.
