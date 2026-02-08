# Building and Running MediGraph with Docker

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

## Quick start

### Option A: Neo4j in Docker (all-in-one)

1. **Create a `.env`** in the project root. To use the **Neo4j container**, either leave `NEO4J_URI` unset or set:

   ```env
   NEO4J_URI=bolt://neo4j:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   ```

2. **Start everything:**

   ```bash
   docker compose up -d --build
   ```

3. **Open:** [http://localhost:3000](http://localhost:3000) · API: [http://localhost:8000](http://localhost:8000) · Neo4j Browser: [http://localhost:7474](http://localhost:7474)

### Option B: Local Neo4j (API + frontend in Docker only)

If **Neo4j is already running on your machine** (not in Docker), the API container can connect to it via `host.docker.internal`.

1. **In the project root `.env`**, point Neo4j at your host and Ollama (if on host):

   ```env
   NEO4J_URI=bolt://host.docker.internal:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   ```

   Use the same user/password as your local Neo4j.

2. **Start only the API and frontend** (do not start the Neo4j container):

   ```bash
   docker compose up -d --build api frontend
   ```

3. **Open:** [http://localhost:3000](http://localhost:3000) · API: [http://localhost:8000](http://localhost:8000). Neo4j stays on your host (e.g. [http://localhost:7474](http://localhost:7474) if you run it locally).

## Build only (no run)

- **Build all images:**
  ```bash
  docker compose build
  ```

- **Build a single service:**
  ```bash
  docker compose build api
  docker compose build frontend
  ```

- **Build with no cache (clean rebuild):**
  ```bash
  docker compose build --no-cache
  ```

## Useful commands

| Command | Description |
|--------|-------------|
| `docker compose up -d` | Start in background |
| `docker compose up -d --build` | Build and start |
| `docker compose down` | Stop and remove containers |
| `docker compose logs -f` | Follow logs (all services) |
| `docker compose logs -f api` | Follow API logs only |
| `docker compose ps` | List running containers |

## Services

| Service   | Port | Description                |
|-----------|------|----------------------------|
| frontend  | 3000 | Next.js app (landing + UI) |
| api       | 8000 | FastAPI backend            |
| neo4j     | 7474, 7687 | Graph database         |

## Frontend API URL

The frontend is built with `NEXT_PUBLIC_API_URL=http://localhost:8000` so the **browser** calls the API on your host. If you run the stack on another machine or port, rebuild the frontend with the correct URL:

```bash
docker compose build frontend --build-arg NEXT_PUBLIC_API_URL=http://your-server:8000
docker compose up -d frontend
```

## Using your Ollama model

- **Local (backend not in Docker):** Install [Ollama](https://ollama.ai), run `ollama serve`, then `ollama pull <model>`. In `backend/.env` set:
  - `LLM_PROVIDER=ollama`
  - `OLLAMA_MODEL=<name>` — use the exact name from `ollama list` (e.g. `llama3.2`, `mistral`, `qwen2.5:7b`).
- **API in Docker, Ollama on host:** In the root `.env` set `OLLAMA_BASE_URL=http://host.docker.internal:11434` (Docker Desktop / Windows/Mac). On Linux use your host IP, e.g. `http://172.17.0.1:11434`. Set `OLLAMA_MODEL` to the model you have.

## Troubleshooting

- **API “Connection refused” from frontend:** Ensure the API container is up (`docker compose ps`) and that `NEXT_PUBLIC_API_URL` matches where the browser can reach the API (e.g. `http://localhost:8000` when testing locally).
- **LLM / “Ollama not available”:** Run `ollama serve` and ensure `OLLAMA_MODEL` in `.env` matches a model from `ollama list`. From Docker, set `OLLAMA_BASE_URL` as above.
- **Neo4j “Connection refused” from API in Docker:** If using **local Neo4j**, set in root `.env`: `NEO4J_URI=bolt://host.docker.internal:7687` and run `docker compose up api frontend` (no neo4j service). Ensure Neo4j is running on your host and listening on port 7687. On Linux, `host.docker.internal` is added via `extra_hosts` in the compose file.
