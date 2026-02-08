# MediGraph

**Intelligent Document Parsing & Knowledge Graph for Healthcare Facility Intelligence**

Built for the **Bridging Medical Deserts** track (Virtue Foundation / Databricks). MediGraph turns messy facility CSV data into a queryable knowledge graph and an agentic AI layer—so planners can ask questions in plain language, see where care exists, and identify gaps and medical deserts.

---

## What it does

- **Upload** facility CSVs (e.g. Virtue Foundation Ghana format); optionally use LLM to extract entities from free-text columns (equipment, procedures, specialties, capabilities).
- **Build** a Neo4j knowledge graph with facilities, locations, equipment, procedures, and typed relationships.
- **Query** in natural language: “Which facilities lack ultrasound?”, “List facilities in Accra with their specialties”—get answers with **citations** and optional **reasoning trace**.
- **Plan** via a dedicated Planning tab (resource allocation, distribution, capacity questions).
- **Visualize** the graph and a **map** of locations; run built-in **medical-deserts** and **equipment-gaps** analysis.

---

## Prerequisites (local models)

The app uses **Ollama** by default for queries and LLM extraction. Install and pull the required model before running:

1. **Install [Ollama](https://ollama.ai)** for your OS.
2. Start Ollama (it often runs in the background after install), or run: `ollama serve`.
3. **Pull the default model:**  
   `ollama pull llama3.2`  
   (Set `OLLAMA_MODEL` in `.env` to match; see [backend/.env.example](backend/.env.example).)
4. Optional: if you use a different model for entity extraction (`OLLAMA_MODEL_EXTRACTOR=qwen2.5:7b`), also run:  
   `ollama pull qwen2.5:7b`

Without Ollama you can use an API provider instead: set `LLM_PROVIDER=gemini` (or `openai` / `anthropic`) and the corresponding API key in your `.env` (see [DOCKER.md](DOCKER.md)).

---

## Quick start

**With Docker (recommended)**

```bash
# Clone, then from project root create a .env (see DOCKER.md for variables)
docker compose up -d --build
# App: http://localhost:3000   API: http://localhost:8000   Neo4j: http://localhost:7474
```

**Local Neo4j + Ollama:** Set in `.env`: `NEO4J_URI=bolt://host.docker.internal:7687`, `OLLAMA_BASE_URL=http://host.docker.internal:11434`, then run:

```bash
docker compose up -d --build api frontend
```

**Without Docker**

- Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`. Requires Neo4j (e.g. `bolt://localhost:7687`) and Ollama (`ollama serve`, `ollama pull llama3.2`). Copy `backend/.env.example` to `backend/.env`.
- Frontend: `cd frontend && npm install && npm run dev`. Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

---

## Tech

| Layer    | Stack |
|----------|--------|
| Frontend | Next.js, React, Tailwind, shadcn/ui, Mapbox |
| Backend  | FastAPI, LangChain, Neo4j |
| LLM      | Ollama (default), or Gemini / OpenAI / Anthropic via env |

---

## Docs

- **[documentation.md](./documentation.md)** — Full description, architecture diagrams, MVP vs track, scalability, evaluation alignment.
- **[DOCKER.md](./DOCKER.md)** — Docker options, env vars, troubleshooting.
