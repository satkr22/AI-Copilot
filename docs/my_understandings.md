1. What is this project?
    - So this project is basically repository aware coding assistant. It indexes the repository using tree sitter, stores the metadata in PostgreSQL, stores the embedding in Qdrant, and it uses a LangGraph workflow  with tools to produce grounded answer with citations.

2. What problem does it solve?
    - The problem with the huge repositories are, it is, it takes a lot of time to understand the code base, to understand a particular function, file, to trace the flow of a function calling, to understand the architecture, to find the exact bug or to trace a error, to create different edge cases for testing. These are the current problems, and this project solves all of these

3. Why is this not a Cursor clone?
    - Well, this project is not a cursor clone. First of all, I'm keeping the architecture simple. I'm not using microservices in my MVP or version one. It increases complexity. It doesn't have advanced features like integrating with any IDE and support of all the languages, and generate advanced code. This project is for understanding of the AI copilots and the tools which I'm gonna use in this, like the workflow of LangGraph, LangChain, PostgreSQL, semantic search, and RAG.

4. What is repository intelligence?
    - So a repository intelligence is a system which indexes the repository files. It converts into a structure which could be traversed and could be analyzed, and different parts of it could be extracted in a seamless manner. It is done by converting it into an AST tree and storing the structure into the knowledge graph. And then that knowledge graph is converted into embeddings and stored in a vector database. And then it can be queried to extract a particular file or a function from the repository. It could be used to create the complete workflow of the system from user input to the final output. It can be used to trace function calls. It gives metadata about functions inside files, like why that function is used, what are its parameters, about classes, yeah, like this.

5. Why Tree-sitter?
    - So, a tree-sitter is basically a tool or library used to convert the source code into CST, Concrete Syntax Tree. It is similar to AST, which is Abstract Syntax Tree, but CST is more precise. It contains the syntax details like commas, colon, parentheses, and other elements, and it can be used to map the source code very precisely. And CST is used for forming the knowledge graph precisely because it contains the source code information to exactly what it is, including every small details.

6. Why PostgreSQL?
    - Why PostgreSQL, not MySQL? Because PostgreSQL has many features which directly supports projects like AI Copilot. For example, it supports JSON. Its concurrency handling model, MVCC, is much more reliable and trusted. It provides features like full-text search. We can even search inside the JSON.It can handle large amount of rows very efficiently because of its internal implementation. It supports a large SQL commands and also supports customization.It even has tools like PGVector which directly supports semantic search in the stored text, which is very useful for AI projects.It support different kind of indexing which makes it faster. For example, Gin indexing makes JSON search very fast.

7. Why Qdrant?
    - LLMs cannot efficiently search large codebases by themselves because they have limited context windows. We convert code and documentation into embeddings and store them in Qdrant. At query time, the user's question is embedded into the same vector space, and Qdrant performs approximate nearest-neighbor search using the HNSW index to retrieve the most semantically relevant chunks. Those chunks are then supplied to the LLM, enabling accurate Retrieval-Augmented Generation (RAG) while keeping latency and token costs low.
    
8. Why LangGraph?
    - So this process is using LangChain applications, it's just not a simple workflow like one prompt given to LLM and it returns the answer using RAG. No. There are many steps and tools involved for answering one question. For example, if user wants or asks to generate a code or ask about the function, then first it will understand the intent. Second, if user wants to understand a particular class, then it will retrieve the exact relevant files. And for understanding, it will again understand the classes inside it, and the functions inside it, and how those functions are called, and what does that function do. That cannot be done in one single prompt. And if the file and the context retrieved is not sufficient, it will go back again to retrieve more context. And at every point, it also remembers the state of the system, like what was the actual user's query, what were the previously retrieved context. All of these things cannot be done in one prompt and LLM memory. It needs a workflow so that it has one state and can move over the state if required. So LangGraph helps to orchestrate all the workflow and tool callings.

9. Why MCP-style tools?
    - "The system has a reusable repository tool layer that encapsulates repository operations. The LangGraph workflow orchestrates reasoning by invoking these tools. Because the tool layer is decoupled from the orchestration logic, it can later be exposed through an MCP server or other interfaces without changing the underlying implementation."

10. Why not Neo4j/Redis/Kafka/Kubernetes?
    - Neo4j – We don’t need a graph database in V1. Our relationship queries (dependencies, imports) are shallow and can be handled by PostgreSQL with foreign keys and JOINs. Adding Neo4j introduces operational complexity and a new query language for marginal gain. We can always add it later if relationship traversal becomes central.

    - Redis – Not needed for caching or task queues yet. V1 is single-user and synchronous; we won’t have heavy background jobs. If we later add async indexing, we might use Redis or a simple queue, but for now it’s overkill.

    - Kafka – Event streaming is far beyond our scale. We don’t need publish‑subscribe between services because we’re using a modular monolith.

    - Kubernetes – Overkill for local development and single‑container deployment. Docker Compose gives us reproducible environments without the complexity of orchestration.