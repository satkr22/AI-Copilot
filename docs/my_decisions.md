Decision: Use modular monolith instead of microservices.
Reason: One developer, simpler deployment, still clean architecture.
Alternative: Microservices.
Why not: Adds distributed system complexity without improving MVP learning value.

Decision: Use PostgreSQL + Qdrant.
Reason: PostgreSQL stores structured metadata; Qdrant stores embeddings.
Alternative: PostgreSQL only or Neo4j.
Why not: PostgreSQL only is weaker for semantic search; Neo4j is unnecessary for V1.