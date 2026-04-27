# Insurance Broker Platform

**Author:** Facundo Braida  
**Date:** 2026-04-27  
**Stack:** Python · FastAPI · SQLModel · PostgreSQL + pgvector · Docker Compose

## Walkthrough recording

https://www.loom.com/share/87a856bb6fd94f87a7b0b5ae37b18924

---

## How to run locally

### Prerequisites

- Docker and Docker Compose

### Steps

```bash
# 1. Clone the repo
git clone "https://github.com/BraidaFac/insurance-broker-api"
cd insurance-broker-api

# 2. Copy the env file and add your OpenRouter key
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY=<your-key>

# 3. Start the stack
docker compose up --build

# 4. Run migrations (first time only)
docker compose exec backend alembic upgrade head

# 5. Seed the database
docker compose exec backend python seeds/seed_data.py

# 6. Generate embeddings for all policies
curl -X POST http://localhost:8000/api/v1/policies/reindex \
  -H "Authorization: Bearer <token>"
```

The API is available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

### Getting a token

```bash
curl -X POST http://localhost:8000/api/v1/login/access-token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changethis"
```

---

## Model choices

**Embedding model:** `text-embedding-3-small` via OpenRouter — strong semantic quality at low cost, 1536 dimensions, same API client as the agent with no extra dependency.

**LLM:** `openai/gpt-4o` via OpenRouter — excellent tool-calling reliability, OpenAI-compatible SDK means zero extra dependencies, and widely proven for structured function calling.

---

## Example: semantic search

```bash
TOKEN="<your-token>"

curl "http://localhost:8000/api/v1/policies/search/semantic?q=cyber+liability+for+small+business&k=3" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**

```json
[
  {
    "id": "a1b2c3d4-...",
    "product_type": "cyber",
    "insurer": "Marsh New Zealand / Beazley",
    "sum_insured_nzd": 500000,
    "description": "Cyber liability and data breach response policy for SMEs...",
    "distance": 0.081
  },
  {
    "id": "e5f6a7b8-...",
    "product_type": "cyber",
    "insurer": "AIG New Zealand",
    "sum_insured_nzd": 1000000,
    "description": "Cyber insurance for professional services firms and healthcare providers...",
    "distance": 0.134
  },
  {
    "id": "c9d0e1f2-...",
    "product_type": "cyber",
    "insurer": "Zurich New Zealand",
    "sum_insured_nzd": 2000000,
    "description": "Comprehensive cyber risk policy for mid-to-large enterprises...",
    "distance": 0.158
  }
]
```

---

## Example: agent

```bash
curl -X POST http://localhost:8000/api/v1/agent/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Which policies best suit a small Auckland café with NZ$850k annual turnover worried about cyber POS breaches and public liability?"}'
```

**Response:**

```json
{
  "answer": "Based on the search results, I recommend two policies for a small Auckland café with NZ$850k turnover:\n\n1. **Vero Insurance NZ — Public Liability (NZ$2M)**: Comprehensive cover for bodily injury and property damage to third parties, including product liability for food sold. Well-suited for high-foot-traffic hospitality with on-site and off-site incidents covered.\n\n2. **Marsh New Zealand / Beazley — Cyber (NZ$500k)**: Specifically designed for SMEs and covers data breach response, ransomware, and regulatory fines under the NZ Privacy Act 2020 — directly addressing the POS breach concern. Includes a 24/7 incident response hotline.\n\nBoth policies are proportionate to the business size and directly address the two risks flagged."
}
```

---

## What I'd do next with another 2 hours

- **Auto-embed on create/update:** currently a policy must be manually reindexed after creation. Calling `embed_text` inside the POST/PATCH route would make policies immediately searchable without the extra step.
- **HNSW index on the embedding column:** pgvector does a full table scan by default. An HNSW index, keeps search fast as the policy catalogue grows.
- **`get_client` tool in the agent:** adding a second tool that retrieves client data (industry, turnover, notes) would let the model personalise recommendations instead of searching by free text alone.
- **Structured agent logging:** logging each tool call with its arguments and the number of results returned is the minimum needed to debug agent behaviour and satisfy audit requirements in a regulated domain like insurance.

---

## Deployment approach

For production I would containerise the backend and deploy it using Docker.
If using Docker Compose, I would place it behind an Nginx reverse proxy handling TLS termination. However, if deploying on ECS or Cloud Run, Nginx is not required since TLS termination and load balancing are handled by the platform.
I would set ENVIRONMENT=production to enforce configuration validation at startup, and store secrets in AWS Secrets Manager or an equivalent secure vault.
Database migrations (Alembic) should be executed as a separate deployment step before releasing the new version to avoid schema drift or runtime conflicts.
For vector storage, I would use a managed Postgres-compatible solution with pgvector enabled (e.g. AWS RDS or Supabase).

---

## Time per step

| Step                      | Actual time |
| ------------------------- | ----------- |
| 1 — Stack running         | ~20 min     |
| 2 — Domain models + CRUD  | ~40 min     |
| 3 — pgvector + embeddings | ~50 min     |
| 4 — Semantic search       | ~20 min     |
| 5 — Agent                 | ~35 min     |
| 6 — README                | ~15 min     |
| **Total**                 | **~3h**     |

---
