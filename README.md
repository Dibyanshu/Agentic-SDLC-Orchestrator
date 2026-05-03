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

The current Python workflow is a deterministic stub that can generate initial PRD sections, pause for HITL, approve into BA, approve into Architecture, and complete. Project records, generated sections, section versions, checkpoints, and HITL refinement logs are now written to MySQL. The LLM and RAG adapters are scaffolded for the next implementation slice.

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

```bash
cp .env.example .env
```

Keep real local secrets such as `OPENAI_API_KEY` in `.env`. The `.env` file is intentionally ignored by git; `.env.example` should stay as the safe template with empty/example values.

Build and start the stack:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up --build -d
```

If Docker fails during the API `dotnet publish` build step with a Go/runtime hook error such as `fatal error: invalid runtime symbol table`, restart Docker Desktop first. If it persists, use the local API publish fallback:

```powershell
& 'C:\Program Files\dotnet\dotnet.exe' publish src/api/AgenticSdlc.Api/AgenticSdlc.Api.csproj -c Release -o src/api/AgenticSdlc.Api/publish
docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.local-api-build.yml up --build -d
```

That fallback builds the API with the local .NET SDK and Docker only packages the published files into the ASP.NET runtime image.

If containers remain stuck in `Created` after that Docker runtime error, Docker Desktop itself needs to be restarted. After restart, clean up stale containers and rerun:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml down --remove-orphans
docker rm focused_chatterjee happy_haibt
docker compose --env-file .env -f infra/docker-compose.yml up --build -d
```

If the normal API SDK build still fails after Docker Desktop restart, use the fallback command:

```powershell
& 'C:\Program Files\dotnet\dotnet.exe' publish src/api/AgenticSdlc.Api/AgenticSdlc.Api.csproj -c Release -o src/api/AgenticSdlc.Api/publish
docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.local-api-build.yml up --build -d
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

If a host port is already allocated, change the matching value in `.env`:

```env
API_HOST_PORT=8080
AGENT_HOST_PORT=8000
CHROMA_HOST_PORT=8002
MYSQL_HOST_PORT=3307
CHROMA_URL=http://localhost:8002
```

Container-to-container traffic still uses internal service names, so changing `CHROMA_HOST_PORT` only affects access from your host machine.

## Local Run

Use local run when you want to iterate on code directly from the workspace. You can still keep MySQL and Chroma in Docker.

Start only the backing services:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d mysql chroma
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

Get workflow status:

```http
GET http://localhost:8080/workflow/<project id>/status
```

Get persisted checkpoints:

```http
GET http://localhost:8080/checkpoints/<project id>
```

Get generated sections:

```http
GET http://localhost:8080/sections/<project id>
```

Get, update, and inspect one section:

```http
GET http://localhost:8080/sections/<project id>/PRD/Features

PUT http://localhost:8080/sections/<project id>/PRD/Features
Content-Type: application/json

{
  "content": "Updated feature description"
}

GET http://localhost:8080/sections/<project id>/PRD/Features/versions
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
docker compose --env-file .env -f infra/docker-compose.yml build
docker compose --env-file .env -f infra/docker-compose.yml up -d
Invoke-RestMethod -Uri http://localhost:8000/health
Invoke-RestMethod -Uri http://localhost:8080/health
& 'C:\Program Files\dotnet\dotnet.exe' build src/api/AgenticSdlc.Api/AgenticSdlc.Api.csproj
python -m compileall src/agent-service/app
```
