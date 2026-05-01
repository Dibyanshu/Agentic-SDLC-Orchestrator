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

## Prerequisites

- Docker Desktop
- Python 3.13+
- .NET SDK

On this machine, the .NET SDK is installed but may not be available as plain `dotnet` in every shell. Use the full path when needed:

```powershell
& 'C:\Program Files\dotnet\dotnet.exe' --info
```

The local build has been verified with SDK `10.0.203` targeting `net8.0`.

## Docker Run

Use Docker when you want the full environment: API, agent service, MySQL, and Chroma.

Copy environment defaults:

```powershell
Copy-Item .env.example .env
```

Build and start the stack:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up --build -d
```

Check containers:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml ps
```

Stop the stack:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml down
```

Reset local Docker volumes, including MySQL and Chroma data:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml down -v
```

Docker ports:

- API: `http://localhost:8080`
- Agent service: `http://localhost:8000`
- Chroma: `http://localhost:8001`
- MySQL: `localhost:3306`

## Local Run

Use local run when you want to iterate on code directly from the workspace. You can still keep MySQL and Chroma in Docker.

Start only the backing services:

```powershell
docker compose --env-file .env.example -f infra/docker-compose.yml up -d mysql chroma
```

Run the Python agent service in terminal 1:

```powershell
cd src/agent-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the .NET API in terminal 2:

```powershell
$env:AGENT_SERVICE_URL = 'http://localhost:8000'
& 'C:\Program Files\dotnet\dotnet.exe' run --project src/api/AgenticSdlc.Api --urls http://localhost:8080
```

If `dotnet` is on your PATH, this shorter command is equivalent:

```powershell
$env:AGENT_SERVICE_URL = 'http://localhost:8000'
dotnet run --project src/api/AgenticSdlc.Api --urls http://localhost:8080
```

Build the .NET API locally:

```powershell
& 'C:\Program Files\dotnet\dotnet.exe' build src/api/AgenticSdlc.Api/AgenticSdlc.Api.csproj
```

Check Python syntax locally:

```powershell
python -m compileall src/agent-service/app
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

Approve three times to walk the current stub workflow from PRD to BA to Architecture to `completed`.

## Verified Commands

The following commands were verified successfully:

```powershell
docker compose --env-file .env.example -f infra/docker-compose.yml build
docker compose --env-file .env.example -f infra/docker-compose.yml up -d
Invoke-RestMethod -Uri http://localhost:8000/health
Invoke-RestMethod -Uri http://localhost:8080/health
& 'C:\Program Files\dotnet\dotnet.exe' build src/api/AgenticSdlc.Api/AgenticSdlc.Api.csproj
python -m compileall src/agent-service/app
```
