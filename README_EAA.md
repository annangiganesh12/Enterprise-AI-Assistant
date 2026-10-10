# Enterprise AI Assistant

An agentic AI assistant that answers questions over **company documents, a relational database, and uploaded datasets**, with long-term memory, access control, guardrails, and an automated evaluation suite.

Ask in plain English and the assistant decides where to look: a hybrid-search RAG pipeline for documents, read-only SQL for company records, an analytics tool that returns tables and charts, or its own memory of you and your past conversations.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [How a Question Is Handled](#how-a-question-is-handled)
- [RAG Pipeline](#rag-pipeline)
- [Tools](#tools)
- [Memory](#memory)
- [Security and Access Control](#security-and-access-control)
- [Guardrails](#guardrails)
- [Evaluation](#evaluation)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Overview](#api-overview)
- [Example Queries](#example-queries)
- [Scope for Improvement and Future Plan](#scope-for-improvement-and-future-plan)

---

## Features

| Capability | What it does |
|---|---|
| **Document Q&A (RAG)** | Answers from uploaded and company-wide PDFs using hybrid search (vector + keyword), Reciprocal Rank Fusion and cross-encoder reranking |
| **Company database queries** | Converts natural-language questions into read-only SQL over departments, employees, leave records, projects, customers and sales |
| **Data analysis and charts** | Runs aggregations and trend analysis on the core tables or on uploaded CSV/Excel files and returns result tables plus matplotlib charts |
| **Smart routing** | An LLM router sends each question to the right source: documents, a tool, memory, or a general answer |
| **Memory** | Per-thread conversation state, long-term user facts, and cumulative cross-conversation summaries |
| **Auth and roles** | JWT authentication, employee and admin roles, admin-only ingestion, per-user document access |
| **Guardrails** | NVIDIA NeMo Guardrails flows (medical/legal/financial advice, jailbreaks, off-topic) plus an output PII scan |
| **Evaluation** | DeepEval suites for retrieval, generation, end-to-end, multi-turn conversation and safety |
| **Observability** | Optional LangSmith tracing |

---

## Architecture

```mermaid
flowchart TD
    U[Client] --> API[FastAPI API layer<br/>JWT authentication]
    API --> G[LangGraph agent]

    G --> M1[Load user memory]
    M1 --> M2[Load conversation memory]
    M2 --> R{Router}

    R -->|documents| RAG[RAG retrieval<br/>hybrid search + rerank]
    R -->|tools| T[Tool agent]
    R -->|memory| GEN[Generate answer]
    R -->|general| GEN
    RAG --> GEN
    T --> TOOLS[SQL tool<br/>Analytics tool<br/>Calculator]
    TOOLS --> T
    T --> GEN

    GEN --> OUT[Response]
    OUT -.background.-> BG[Update user memory<br/>and conversation summary]

    G <--> PG[(PostgreSQL<br/>pgvector + checkpoints)]
    RAG <--> PG
    TOOLS <--> PG
    BG --> PG
```

Everything lives in a single PostgreSQL database: users, documents, vector chunks (pgvector), company tables, uploaded datasets, memories and LangGraph checkpoints.

---

## How a Question Is Handled

1. The request arrives at `GET /api/v1/documents/rag` with a `query` and a `thread_id`, authenticated by JWT.
2. The agent loads the user's long-term memory and the cumulative conversation summary.
3. An LLM **router** (structured output) picks exactly one route:
   - **RAG:** the answer is in the user's documents or the company knowledge base. The router is told whether the user has uploaded documents, so it prefers their own data over general knowledge.
   - **TOOL:** analytics for reports, trends and charts; SQL for single factual lookups; calculator for exact math.
   - **MEMORY:** facts stored about the user.
   - **CONVERSATION_MEMORY:** information from earlier conversations.
   - **GENERAL:** unrelated to documents, tools or memory.
4. For tool routes, the tool agent selects a tool, executes it, and loops until it has what it needs.
5. The final answer is generated and returned.
6. After responding, memory updates run in a **background task**, so the user is not kept waiting.

Each thread is persisted with the LangGraph PostgreSQL checkpointer, so conversations can be resumed.

---

## RAG Pipeline

**Ingestion (admin only)**

```
PDF → text extraction → chunking (1250 chars, 300 overlap)
    → all-MiniLM-L6-v2 embeddings (384-d) → PostgreSQL + pgvector
```

**Retrieval**

```
query → vector search (cosine) ┐
                               ├→ Reciprocal Rank Fusion → cross-encoder rerank
query → full-text search ──────┘     (ms-marco-MiniLM-L-6-v2)  top 20 → top 10 → LLM
```

Design details:

- **Hybrid search** combines semantic similarity with PostgreSQL full-text matching.
- **SHA-256 file hashing** avoids re-embedding duplicate uploads.
- **Strategy ID** (chunk size, overlap, embedding model) triggers re-processing when settings change.
- **Scoped results:** retrieval returns the user's own documents plus documents marked as global.

---

## Tools

| Tool | Purpose | How it works |
|---|---|---|
| `company_sql_tool` | Single-value factual lookups on the company database | The LLM generates SQL from the schema, a validator allows `SELECT` only and rejects write/DDL keywords, then the result is turned into an answer |
| `analytics_tool` | Reports, aggregations, trends and charts | The LLM chooses the table (core or uploaded), writes SQL and matplotlib code, executes it, and returns the result table, notes and a base64 chart |
| `calculator` | Exact arithmetic | Evaluates an expression with built-ins disabled |

### Uploaded datasets

An admin can upload a CSV or Excel file. It is cleaned with pandas, imported as its own PostgreSQL table, and registered with metadata (name, table, uploader, content hash, global flag). Duplicate files are detected by hash and reused. Datasets can be **global** (visible company-wide) or **private**, and the analytics tool can query them like any other table.

### Company data

The core database includes `departments`, `employees`, `leave_records`, `projects`, `customers` and `sales`, with a seed script for sample data.

---

## Memory

| Layer | What it stores | Where |
|---|---|---|
| **Thread memory** | Conversation state for each thread | LangGraph PostgreSQL checkpointer |
| **Long-term user memory** | One durable fact or preference per turn, extracted by an LLM that is told not to store document facts, temporary questions or general knowledge | `user_memories` table |
| **Conversation memory** | A cumulative summary of past conversations, compressed when it grows past 6000 characters | `conversation_memories` table |

Memory writes run in the background, so response latency is unaffected.

---

## Security and Access Control

- **Authentication:** JWT bearer tokens with hashed passwords (register, login, `/me`).
- **Roles:** `employee` and `admin`. Only admins can ingest documents or datasets and change user roles.
- **Admin cap:** a configurable maximum number of administrators (`MAX_ADMINS`, default 5).
- **Data isolation:** document retrieval is scoped to the user's own documents plus explicitly global ones.
- **Database safety:** generated SQL must be a `SELECT`; write and DDL keywords are rejected.
- **Configuration:** secrets are loaded from environment variables through pydantic settings.

---

## Guardrails

Implemented with **NVIDIA NeMo Guardrails** (Colang flows) in `app/guardrails/`:

- Declines professional **medical, legal and financial advice**
- Blocks **jailbreak** attempts and persona changes, including attempts to reveal the system prompt
- Declines **off-topic** requests
- Scans responses for **PII** (emails, phone numbers, API keys) and returns a safe fallback message
- Falls back safely if the guardrail layer itself errors

The `GuardrailsManager` is a reusable module. Connecting it directly into the chat request path is part of the [future plan](#scope-for-improvement-and-future-plan).

---

## Evaluation

Quality is measured with **[DeepEval](https://github.com/confident-ai/deepeval)**. Synthetic test sets ("goldens") are generated from a PDF using a local embedding model, so generation needs no embedding API cost.

| Suite | Metrics |
|---|---|
| **Retrieval** | Contextual Recall, Contextual Precision |
| **Generation** | Faithfulness, Answer Relevancy, Answer Correctness |
| **End-to-end** | Answer Correctness, Answer Relevancy |
| **Conversational** | Conversation Completeness, Turn Relevancy on simulated multi-turn scenarios |
| **Safety** | Toxicity, PII Leakage, plus custom GEval metrics for Non-Advice, Bias and Role Adherence on 10 adversarial prompts |

Pass thresholds are 0.7 (0.5 for safety metrics). Each run writes a JSON report.

---

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, SQLAlchemy, Pydantic, Alembic
- **Agent framework:** LangChain, LangGraph, LangGraph Postgres checkpointer
- **LLMs:** Google Gemini through LangChain; OpenRouter for the guardrails model
- **Retrieval:** PostgreSQL + pgvector, sentence-transformers, cross-encoder reranker, pypdf
- **Data analysis:** pandas, matplotlib, openpyxl
- **Safety and quality:** NVIDIA NeMo Guardrails, DeepEval
- **Observability:** LangSmith (optional)

---

## Project Structure

```
.
├── app/
│   ├── main.py                 # FastAPI app, routers, graph + checkpointer startup
│   ├── api/v1/endpoints/       # auth, documents, ingest, admin endpoints
│   ├── authentication/         # JWT, password hashing, role dependencies
│   ├── core/config.py          # environment-based settings
│   ├── database/               # engine, session, base
│   ├── guardrails/             # NeMo Guardrails config, flows, manager
│   ├── langgraph/              # graph, state, router and node functions
│   ├── models/                 # SQLAlchemy models (users, docs, chunks, memories, company data)
│   ├── schemas/                # Pydantic schemas
│   ├── scripts/                # seed_company_data.py
│   ├── services/               # chat, retrieval, document, dataset, memory services
│   ├── tools/                  # sql_tool, analytics_tool, calculator
│   └── utils/                  # embeddings, reranker, PDF loader
├── alembic/                    # database migrations
├── evals/
│   ├── datasets/               # golden dataset generators
│   ├── metrics/                # retrieval, generation, e2e, conversational, safety evals
│   └── utils/                  # local embedding model for DeepEval
├── init_db.py                  # create tables from models
├── requirements.txt
└── alembic.ini
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL with the [pgvector](https://github.com/pgvector/pgvector) extension
- API keys for Google Gemini, OpenRouter and Tavily

### 1. Clone and install

```bash
git clone https://github.com/annangiganesh12/Enterprise-AI-Assistant.git
cd Enterprise-AI-Assistant
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/enterprise_ai
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

GOOGLE_API_KEY=your-gemini-key
OPENROUTER_API_KEY=your-openrouter-key
TAVILY_API_KEY=your-tavily-key

# Required by the settings class; placeholders are fine until these integrations are built
JIRA_URL=
JIRA_API_TOKEN=
GOOGLE_DRIVE_URL=
GOOGLE_ACCESS_TOKEN=

# Optional
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=Enterprise-AI-Assistant
MAX_ADMINS=5
```

### 3. Set up the database

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then create the tables with either approach:

```bash
python init_db.py          # create tables from the models
# or
alembic upgrade head       # apply migrations
```

Optionally load sample company data:

```bash
python -m app.scripts.seed_company_data
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

Interactive docs are available at `http://localhost:8000/docs`.

### 5. Try it

1. `POST /api/v1/auth/register` to create a user. Create your first user with the `admin` role, since ingestion is admin-only.
2. `POST /api/v1/auth/login` to get a bearer token, and use it on the other endpoints.
3. `POST /api/v1/ingest` with a PDF, CSV or Excel file (admin only).
4. `GET /api/v1/documents/rag?query=...&thread_id=...` to chat with the assistant.

---

## API Overview

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/` , `/health` | Public | Welcome message and health check |
| POST | `/api/v1/auth/register` | Public | Create a user |
| POST | `/api/v1/auth/login` | Public | Get a JWT access token |
| GET | `/api/v1/auth/me` | User | Current user profile |
| PATCH | `/api/v1/admin/users/{user_id}/role` | Admin | Change a user's role (respects `MAX_ADMINS`) |
| POST | `/api/v1/ingest` | Admin | Unified ingestion for PDFs and CSV/Excel datasets (`is_global`, `document_type`, `department`, `category` options) |
| POST | `/api/v1/documents/upload` | Admin | Upload a PDF document |
| GET | `/api/v1/documents/search` | User | Vector search |
| GET | `/api/v1/documents/keyword-search` | User | Full-text search |
| GET | `/api/v1/documents/hybrid-search` | User | Vector + keyword search with RRF |
| GET | `/api/v1/documents/reranking` | User | Hybrid search with cross-encoder reranking |
| GET | `/api/v1/documents/rag` | User | Full agent: routing, tools, memory and answer generation |

---

## Running the Evaluations

Generate test sets, then run the metric suites. Edit the document path inside the dataset generator scripts first (`evals/datasets/generate_*.py`) to point at your own PDF.

```bash
# 1. Generate goldens
python -m evals.datasets.generate_retriever_dataset
python -m evals.datasets.generate_rag_dataset
python -m evals.datasets.generate_e2e_dataset

# 2. Run evaluations
python -m evals.metrics.eval_retrieval
python -m evals.metrics.eval_generation
python -m evals.metrics.eval_e2e
python -m evals.metrics.eval_conversational
python -m evals.metrics.eval_safety
```

---

## Example Queries

- "What does the uploaded handbook say about leave policy?" → RAG
- "How many employees are in the AI department?" → SQL tool
- "Show monthly sales trends and plot them." → Analytics tool with a chart
- "What is the attrition rate by department in the dataset I uploaded?" → Analytics tool on an uploaded dataset
- "What is 18% of 45,250?" → Calculator
- "What did I tell you about my preferences?" → Memory

---

## Scope for Improvement and Future Plan

The project is a working end-to-end prototype. The plan below describes how it can be taken to production level.

### Performance and scalability

- **Caching (Redis):** cache query embeddings, retrieval results, SQL and analytics results, and frequent LLM responses; cache user memory lookups per session.
- **Async database connections:** move to SQLAlchemy async engine with an async PostgreSQL driver and tuned connection pooling, so request handling does not block on database calls. Pair it with async LLM and tool calls.
- **Rate limiting:** per-user and per-IP limits on the API (for example with a Redis-backed limiter) to protect LLM budgets and prevent abuse.
- **Load balancing and horizontal scaling:** run multiple stateless API replicas behind a load balancer (Nginx, a cloud load balancer or a Kubernetes ingress). Conversation state already lives in PostgreSQL checkpoints, which makes this straightforward.
- **Background job queue:** move document and dataset ingestion (chunking, embedding) to workers such as Celery or ARQ, with progress status for the user.
- **Streaming responses:** stream tokens to the client to improve perceived latency.
- **Vector search tuning:** add pgvector HNSW or IVFFlat indexes and a full-text GIN index for faster retrieval at scale; consider a dedicated vector store if data grows very large.
- **Model efficiency:** serve the embedding and reranker models once per worker, batch requests, and add model fallbacks and retries for LLM providers.

### Security and reliability

- Connect the `GuardrailsManager` directly into the chat request path and re-run the safety evals against the guarded pipeline.
- Run LLM-generated plotting code in a sandbox, use a read-only database role for the SQL tools, and add stronger SQL parsing and validation.
- Restrict role selection at registration, add refresh tokens, and move secrets to a secrets manager.
- Add request validation limits (file size and type checks), audit logging, and retention policies for stored memory.
- Add health and readiness checks, timeouts, retries and graceful degradation when an LLM provider is down.

### DevOps

- **Docker:** multi-stage Dockerfile for the API, plus a `docker-compose` setup with PostgreSQL (pgvector), Redis and the API for one-command local development.
- **Kubernetes:** deployment manifests or a Helm chart with separate API and worker deployments, ConfigMaps and Secrets, liveness and readiness probes, resource limits, a horizontal pod autoscaler, and an ingress with TLS.
- **CI/CD (GitHub Actions):** on every pull request run linting, type checks and unit tests; run the DeepEval suites as a quality gate; on merge build and push the Docker image, run database migrations, and deploy to staging, then production with an approval step.
- **Infrastructure as code:** define cloud infrastructure (database, cluster, networking) with Terraform.
- **Environments:** separate dev, staging and production configurations with environment-specific secrets.

### Observability and quality

- Structured logging, metrics (Prometheus and Grafana) and distributed tracing, building on the existing optional LangSmith tracing.
- Record baseline evaluation scores, track them over time, and alert on regressions.
- Add unit and integration tests for the API, tools and retrieval, and load tests to find bottlenecks before release.

### Product features

- Add thread summarization to the graph for very long conversations.
- Extend tools to more enterprise systems such as Jira and Google Drive.
- Build a web front end with chat history, file upload and chart display.
- Add feedback collection (thumbs up/down) to improve retrieval and prompts over time.
