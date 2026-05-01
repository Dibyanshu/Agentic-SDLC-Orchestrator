# Agentic SDLC Orchestrator

This repository contains the Phase 1 design and implementation plan for an Agentic SDLC Orchestrator.

Start here:

- [Product Requirements](PRD.md)
- [High Level Design](HLD.md)
- [Low Level Design](LLD.md)
- [Feature Breakdown](Feature.md)
- [Executable Implementation Plan](IMPLEMENTATION_PLAN.md)

## Current Implementation

The first implementation slice has been scaffolded:

- `.NET 8` API control plane in `src/api/AgenticSdlc.Api`
- Python FastAPI agent service in `src/agent-service`
- MySQL migration scripts in `infra/mysql/migrations`
- Docker Compose runtime in `infra/docker-compose.yml`

The current Python workflow is a deterministic stub that can generate initial PRD sections, pause for HITL, approve into BA, approve into Architecture, and complete. The LLM, RAG, and durable persistence adapters are scaffolded for the next implementation slice.

## Local Setup

Copy environment defaults:

```powershell
Copy-Item .env.example .env
```

Start local infrastructure and services:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up --build
```

Run the Python agent service directly:

```powershell
cd src/agent-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run the .NET API directly:

```powershell
dotnet run --project src/api/AgenticSdlc.Api
```

## Smoke Test

API health:

```http
GET http://localhost:8080/health
```

Agent service health:

```http
GET http://localhost:8000/health
```

Create a project through the API:

```http
POST http://localhost:8080/projects
Content-Type: application/json

{
  "name": "Demo",
  "goal": "Generate early SDLC artifacts"
}
```

Start workflow:

```http
POST http://localhost:8080/workflow/start
Content-Type: application/json

{
  "projectId": "<project id>",
  "input": "Build an agentic SDLC orchestrator"
}
```

Approve HITL:

```http
POST http://localhost:8080/hitl/action
Content-Type: application/json

{
  "projectId": "<project id>",
  "action": "approve"
}
```
