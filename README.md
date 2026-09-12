# MockForge AI 🚀
### Intelligent Stateful API Virtualization & Multi-Agent Testing Platform

MockForge AI is a state-of-the-art API virtualization and testing platform. It transforms OpenAPI 3.x specifications into **live, stateful, parent-child relational mock servers** featuring **sub-10ms HTTP response times**, **chaos engineering fault injection**, and a **5-Agent AI Compiler Swarm** with Bring Your Own Key (BYOK) support for Google Gemini, Groq, Ollama, and OpenAI.

---

## 🌟 Key Features

1. **Dynamic Catch-All Router (`/mock/{project_id}/{path:path}`)**:
   - Zero server restarts or route re-registration required. Instant URL matching for `GET`, `POST`, `PUT`, `PATCH`, `DELETE` routes directly upon spec upload.
2. **Relational Parent-Child State Engine & FK Validation**:
   - Automatically parses `*_id` / `*Id` fields and builds an in-memory relationship graph index. Rejects orphan child entities (`POST /orders` referencing missing `user_id`) with `422 Unprocessable Entity`.
   - Supports nested parent-child queries: `GET /users/usr_123/orders` filters child orders belonging to `usr_123`.
3. **Chaos Engineering & Resilience Injection**:
   - Inject HTTP status overrides (`500 Internal Error`, `429 Rate Limit`, `503 Service Unavailable`), latency spikes (e.g. 500ms delay), or malformed JSON payloads per endpoint.
4. **5-Agent AI Compiler Swarm (Bring Your Own Key)**:
   - **Spec Intelligence Agent**: Ingests specs & extracts Entity-Relationship Diagrams (ERD).
   - **State Machine Agent**: Infers entity lifecycle states (`CREATED` $\rightarrow$ `PAID` $\rightarrow$ `SHIPPED`) and transition guard rules.
   - **Scenario Agent**: Synthesizes end-to-end multi-step integration test workflows.
   - **Chaos Agent**: Recommends resilience injection rules for third-party endpoints.
   - **Critic Agent (Pure Code Gatekeeper)**: Fast in-memory validator ensuring 0% hallucinated API endpoints.
5. **BYOK Provider Factory (Model Agnostic)**:
   - Connect **Google Gemini** (`gemini-2.0-flash`), **Groq** (`llama-3.3-70b-versatile`), **Ollama** (Local/Free `llama3.3:8b`), or **OpenAI** (`gpt-4o-mini`).
   - Includes **Offline Deterministic Fallback** so the system runs without requiring API keys or internet access.
6. **Glassmorphic Modern Web Dashboard**:
   - Built with React + Vite featuring live spec ingestion, entity graph visualizer, Postman-style interactive REST client, chaos control panel, and AI scenario runner.

---

## 🛠️ Quick Start Guide

### 1. One-Click Launcher (Windows)
Double click `start_mockforge.bat` or run:
```cmd
start_mockforge.bat
```

### 2. Manual Startup

**Terminal 1 — FastAPI Backend Engine:**
```bash
cd backend
python -m uvicorn app.main:app --port 8000 --reload
```

**Terminal 2 — React Dashboard:**
```bash
cd frontend
npm run dev
```

Dashboard UI: [http://localhost:3000](http://localhost:3000)  
Backend API: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧪 Running Automated Tests

MockForge AI includes 5 comprehensive automated pytest suites:

```bash
cd backend
python -m pytest -v tests/
```

Test Coverage:
* `test_mock_engine.py`: Core CRUD mock engine & OpenAPI parsing.
* `test_phase2_relational.py`: Foreign key indexing & parent-child nested route resolution (`GET /users/{id}/orders`).
* `test_phase3_chaos.py`: Status code 500 overrides, latency injection, and malformed payload injection.
* `test_phase4_agents.py`: Multi-agent pipeline compilation, ERD graph extraction, and scenario generation.
* `test_yaml_fixture.py`: Real-world OpenAPI `.yaml` file ingestion from disk.

---

## 🐋 Docker Deployment

```bash
docker-compose up --build
```

---

## 📄 License
MIT License. Created with Antigravity AI.
