# Day 1 Plan: Project Foundation

## Summary

Today you start building the **foundation only**. No LangGraph, no Tree-sitter, no RAG yet. The goal is to create a clean working base so every future feature has a proper place to live.

Your repo currently has only docs, an empty `frontend/`, and a nearly empty `backend/`, so Day 1 is about setting up the actual application skeleton.

## First: Finish Day 0 Cleanup

Before coding, update your notes:

- Complete `docs/my_understandings.md` question 10: why not Neo4j, Redis, Kafka, Kubernetes.
- Correct this idea: do not say “knowledge graph is converted into embeddings.”
- Better wording: “Code chunks are embedded into Qdrant; structured repository metadata is stored in PostgreSQL.”

## Learn Today

Understand these before writing much code:

- What a **modular monolith** is.
- Why FastAPI routes should not contain business logic.
- Why we separate `api`, `schemas`, `models`, `services`, and `db`.
- What Docker Compose does.
- Why PostgreSQL and Qdrant run as separate containers.
- What a health check endpoint proves.

## Build Today

Create the minimum working foundation:

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
    main.py

frontend/
  src/
    pages/
    components/
    api/
    App.tsx
    main.tsx

docker-compose.yml
README.md
.env.example
```

Backend must have:

- FastAPI app.
- `GET /health`.
- Basic config loading from environment variables.
- Database connection setup placeholder.
- Clean folder structure.

Frontend must have:

- React + TypeScript setup.
- One simple page showing app name.
- A call to backend `/health`.
- Display backend status.

Docker Compose must include:

- `postgres`
- `qdrant`
- `backend`
- `frontend`

## Do Not Build Today

Do not add:

- LangGraph
- LangChain
- Tree-sitter
- embeddings
- repository upload
- authentication
- complex UI
- database schema for all future tables

Those come later. Today is boring on purpose. Good foundations are quiet.

## Day 1 Success Criteria

You are done today when:

- Backend starts successfully.
- Frontend starts successfully.
- PostgreSQL container starts.
- Qdrant container starts.
- Frontend can show backend health status.
- You can explain the folder structure.
- You can explain why this is a modular monolith.

## Interview Explanation To Practice

Say this out loud after finishing:

> “I started with a modular monolith foundation. FastAPI owns the backend API and service layer, React owns the user interface, PostgreSQL stores structured metadata, and Qdrant will store embeddings. Docker Compose gives me a reproducible local environment without adding Kubernetes or microservice complexity.”

## End Of Day Notes

Add one decision to your decision journal:

```text
Decision: Start with a minimal FastAPI + React + PostgreSQL + Qdrant foundation.

Reason:
The AI features depend on a stable application base. Building LangGraph or Tree-sitter first would create isolated experiments instead of a production-style system.

Alternative:
Start directly with AI/repository parsing.

Why not:
That would be faster for demos but weaker for architecture, maintainability, and interview explanation.

Consequence:
Day 1 has less AI code, but the project becomes easier to extend cleanly.
```
