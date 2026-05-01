# Agentic SDLC Orchestrator - Executable Implementation Plan

## 0. Current Repository State

The repository currently contains product and design documentation only:

- `PRD.md`
- `HLD.md`
- `LLD.md`
- `Feature.md`
- empty `README.md`

There is no application source code yet. This plan therefore starts from scaffolding and proceeds through executable vertical slices.

## 1. Target Phase 1 Architecture

Build four runnable components:

1. `.NET 8 API` as the control plane for projects, sections, HITL actions, workflow start/resume, and logs.
2. `Python FastAPI Agent Service` for LangGraph orchestration, agent execution, context building, regeneration planning, LLM calls, and checkpointing.
3. `MySQL` for projects, artifacts, sections, versions, checkpoints, refinement logs, and LLM logs.
4. `Vector DB` for controlled RAG. Use Chroma locally for Phase 1 unless Pinecone is explicitly required later.

Recommended repository layout:

```text
src/
  api/
    AgenticSdlc.Api/
    AgenticSdlc.Api.Tests/
  agent-service/
    app/
      api/
      graph/
      graph/nodes/
      agents/
      context/
      llm/
      persistence/
      regeneration/
      schemas/
    tests/
  shared/
    contracts/
infra/
  docker-compose.yml
  mysql/
    migrations/
docs/
  api/
  decisions/
```

## 2. Milestone Execution Order

### Milestone 1 - Repository and Local Runtime Scaffold

Goal: make the repo runnable before business logic is added.

Tasks:

1. Create `.NET 8` Web API project under `src/api/AgenticSdlc.Api`.
2. Create `.NET` test project under `src/api/AgenticSdlc.Api.Tests`.
3. Create Python FastAPI project under `src/agent-service`.
4. Add `infra/docker-compose.yml` with:
   - `mysql`
   - `chroma`
   - `agent-service`
   - `api`
5. Add root `.env.example`.
6. Update `README.md` with setup and run commands.

Suggested commands:

```powershell
dotnet new webapi -n AgenticSdlc.Api -o src/api/AgenticSdlc.Api
dotnet new xunit -n AgenticSdlc.Api.Tests -o src/api/AgenticSdlc.Api.Tests
dotnet new sln -n AgenticSdlc
dotnet sln AgenticSdlc.sln add src/api/AgenticSdlc.Api/AgenticSdlc.Api.csproj
dotnet sln AgenticSdlc.sln add src/api/AgenticSdlc.Api.Tests/AgenticSdlc.Api.Tests.csproj
```

Acceptance criteria:

- `docker compose up` starts MySQL and Chroma.
- `.NET API` exposes `GET /health`.
- `Python Agent Service` exposes `GET /health`.
- README contains first-run instructions.

## 3. Milestone 2 - Database Foundation

Goal: establish persistent, versioned project state.

Tasks:

1. Add database migrations for:
   - `projects`
   - `artifacts`
   - `sections`
   - `section_versions`
   - `refinement_logs`
   - `checkpoints`
   - `llm_logs`
   - `llm_context_chunks`
2. Add indexes for:
   - `project_id`
   - `artifact_id`
   - `section_id`
   - `node_name`
   - `created_at`
3. Implement repository layer in `.NET API`.
4. Implement equivalent persistence client in Python for graph checkpoint and LLM logging writes.

Minimum schema corrections from current docs:

- Keep current content in `sections`.
- Store immutable history in `section_versions`.
- Use `snake_case` table names consistently.
- Add `updated_at` where records are mutable.
- Add foreign keys for traceability.

Acceptance criteria:

- Fresh database can be created from migrations.
- `POST /projects` persists a project.
- `GET /projects/{id}` returns the created project.
- Section updates create a new `section_versions` row.

## 4. Milestone 3 - .NET Control Plane API

Goal: expose stable APIs used by UI and orchestration clients.

Endpoints:

```text
POST /projects
GET  /projects/{projectId}

POST /workflow/start
POST /workflow/resume
GET  /workflow/{projectId}/status

GET  /sections/{projectId}
GET  /sections/{projectId}/{artifactType}/{sectionName}
PUT  /sections/{sectionId}
GET  /sections/{sectionId}/versions

POST /hitl/action

GET  /logs/llm/{projectId}
GET  /checkpoints/{projectId}
```

Tasks:

1. Define request/response DTOs in `src/shared/contracts`.
2. Implement validation for required IDs, action enums, artifact types, and section names.
3. Add typed HTTP client from `.NET API` to Python Agent Service.
4. Add API integration tests using a test database.

Acceptance criteria:

- All endpoints return structured error responses.
- Invalid HITL actions fail with `400`.
- API can call agent-service health endpoint.
- Tests cover project creation, section update, and HITL validation.

## 5. Milestone 4 - Python Agent Service Skeleton

Goal: make workflow execution callable independently of the .NET API.

Modules:

```text
app/
  main.py
  api/routes.py
  schemas/state.py
  graph/graph_builder.py
  graph/nodes/manager_node.py
  graph/nodes/pm_node.py
  graph/nodes/ba_node.py
  graph/nodes/architect_node.py
  graph/nodes/hitl_node.py
  agents/base_agent.py
  agents/pm_agent.py
  agents/ba_agent.py
  agents/architect_agent.py
  context/context_builder.py
  context/rag_retriever.py
  llm/llm_client.py
  llm/prompt_templates.py
  persistence/mysql_client.py
  persistence/checkpoint_store.py
  logging/llm_logger.py
  regeneration/dependency_resolver.py
  regeneration/regeneration_planner.py
```

Agent-service endpoints:

```text
POST /workflow/start
POST /workflow/resume
POST /workflow/hitl
GET  /workflow/{projectId}/state
GET  /health
```

Acceptance criteria:

- Agent service can initialize an `AgentState`.
- LangGraph compiles.
- `manager_node -> pm_node -> hitl_node` executes and pauses.
- Checkpoint is saved after each node.

## 6. Milestone 5 - First Vertical Slice: Project to PRD to HITL

Goal: deliver one complete working path before adding BA and architecture.

Flow:

```text
POST /projects
POST /workflow/start
agent-service runs manager_node
agent-service runs pm_node
PRD sections are stored
checkpoint is stored
workflow pauses at hitl_node
GET /sections/{projectId} returns PRD sections
POST /hitl/action approve moves to next stage later
```

PM output sections:

- `PRD.Overview`
- `PRD.Features`
- `PRD.UserFlow`

Tasks:

1. Implement PM prompt template.
2. Implement structured JSON response parsing.
3. Validate PM output before saving.
4. Log every LLM call.
5. Add cache key generation using `hash(prompt + context_payload)`.

Acceptance criteria:

- A project can generate PRD sections.
- Invalid LLM JSON is logged and retried up to 2 times.
- LLM log includes prompt, response, token estimates, status, latency, and cache metadata.
- Workflow status reports `paused_for_hitl`.

## 7. Milestone 6 - HITL Approve/Edit/Regenerate

Goal: make human control real and auditable.

HITL actions:

1. `approve`: move to next planned node.
2. `edit`: update selected section and create version history.
3. `regenerate`: create regeneration plan and run selected node(s).

Tasks:

1. Implement `POST /hitl/action` in `.NET API`.
2. Persist `refinement_logs`.
3. Implement Python `/workflow/hitl`.
4. Implement state transition logic after HITL.
5. Enforce max refinement loops per stage: `2`.

Acceptance criteria:

- Approving PRD moves workflow to BA stage.
- Editing `PRD.Features` creates a new version.
- Regenerating a section creates an LLM log and new section version.
- Exceeding max refinement loops returns a controlled error.

## 8. Milestone 7 - BA and Architect Agents

Goal: complete the main deterministic workflow.

BA output sections:

- `BA.UserStories`
- `BA.AcceptanceCriteria`

Architecture output sections:

- `ARCH.APIs`
- `ARCH.DBSchema`
- `ARCH.HLD`
- `ARCH.LLD`

Tasks:

1. Implement BA prompt template using PRD sections.
2. Implement Architect prompt template using BA sections and PRD summary.
3. Add graph routing:
   - PRD HITL approval -> `ba_node`
   - BA HITL approval -> `architect_node`
   - Architecture HITL approval -> workflow complete
4. Persist checkpoints at every transition.

Acceptance criteria:

- Full workflow can run from project input to PRD, BA, and Architecture artifacts.
- Workflow pauses after each stage.
- Approving all stages marks workflow as `completed`.

## 9. Milestone 8 - Section-wise Regeneration

Goal: regenerate only the required sections and downstream dependencies.

Hardcoded Phase 1 dependency map:

```text
PRD.Features     -> BA.UserStories -> ARCH.APIs -> ARCH.DBSchema
BA.UserStories   -> ARCH.APIs -> ARCH.DBSchema
ARCH.APIs        -> ARCH.DBSchema
```

Tasks:

1. Implement `dependency_resolver.py`.
2. Implement `regeneration_planner.py`.
3. Add `single` mode:
   - regenerate only selected section's owning node.
4. Add `cascade` mode:
   - regenerate dependent sections in graph order.
5. Store regeneration plan in checkpoint state.

Acceptance criteria:

- `single` regeneration of `PRD.Features` updates only PRD output.
- `cascade` regeneration of `PRD.Features` updates BA user stories and architecture dependencies.
- Regeneration plan is visible through workflow status.

## 10. Milestone 9 - Controlled RAG

Goal: support document and screenshot context without giving agents direct retrieval control.

Endpoints:

```text
POST /rag/sources
GET  /rag/sources/{projectId}
DELETE /rag/sources/{sourceId}
```

Tasks:

1. Add upload handling in `.NET API`.
2. Add ingestion endpoint in Python Agent Service.
3. Implement parsers:
   - TXT first
   - PDF second
   - DOCX third
   - OCR screenshot last
4. Chunk parsed text.
5. Generate embeddings.
6. Store chunks in Chroma with project, stage, and source tags.
7. Retrieve top 5, filter to top 3 in Context Builder.
8. Deduplicate chunks before prompt construction.

Acceptance criteria:

- Uploaded TXT document can influence PRD generation.
- Context Builder returns at most 3 chunks.
- LLM logs record which chunks were injected through `llm_context_chunks`.
- Agents do not call retrieval directly.

## 11. Milestone 10 - Cost Controls and Observability

Goal: make usage measurable and bounded.

Tasks:

1. Enforce token budgets:
   - PM: `3000`
   - BA: `3000`
   - Architect: `4000`
2. Add context truncation/summarization guard.
3. Add response cache table or Redis later; start with MySQL-backed cache if Redis is not introduced.
4. Add metrics endpoint:

```text
GET /metrics/workflow/{projectId}
```

Metrics:

- total input tokens
- total output tokens
- estimated cost
- latency per node
- cache hit count
- refinement count

Acceptance criteria:

- Token budget violations fail before LLM call.
- Repeated identical prompt/context returns cached response.
- Project-level metrics can be queried.

## 12. Milestone 11 - Hardening and Developer Experience

Goal: make the system reliable enough for demos and iteration.

Tasks:

1. Add structured logging in both services.
2. Add correlation ID per workflow execution.
3. Add OpenAPI docs for both APIs.
4. Add end-to-end smoke test:

```text
create project -> start workflow -> generate PRD -> approve -> generate BA -> approve -> generate architecture -> approve -> completed
```

5. Add CI workflow:
   - dotnet build
   - dotnet test
   - python lint
   - python test
   - docker compose config

Acceptance criteria:

- One command starts local runtime.
- One command runs all tests.
- Failed LLM calls are visible in logs.
- Checkpoint resume works after service restart.

## 13. Implementation Backlog

### P0 - Must Have for Phase 1 Demo

- Repo scaffold
- Docker Compose with MySQL and Chroma
- Project API
- Section API with versioning
- Workflow start/resume
- LangGraph skeleton
- PM, BA, Architect nodes
- HITL approve/edit/regenerate
- LLM logging
- Checkpointing
- Hardcoded dependency-based regeneration

### P1 - Should Have

- TXT/PDF/DOCX ingestion
- Chroma retrieval
- Token budget enforcement
- Response caching
- Metrics endpoint
- End-to-end smoke tests

### P2 - Later

- OCR screenshots
- Neo4j dependency graph
- JWT/RBAC
- Redis cache
- Advanced RAG ranking
- Critic/validation agent
- UI frontend

## 14. Recommended First Sprint

Sprint length: 1 week.

Deliverable: first vertical slice from project creation to PRD generation and HITL pause.

Day-by-day plan:

1. Day 1: scaffold `.NET API`, Python Agent Service, Docker Compose, README.
2. Day 2: database migrations and project/section persistence.
3. Day 3: Python LangGraph skeleton and checkpoint save.
4. Day 4: PM agent, prompt template, LLM client, LLM logging.
5. Day 5: wire `.NET API` to agent service, run start workflow, verify PRD sections.

Sprint demo script:

```powershell
docker compose up -d
dotnet run --project src/api/AgenticSdlc.Api
uvicorn app.main:app --reload --app-dir src/agent-service
```

Then call:

```http
POST /projects
POST /workflow/start
GET /sections/{projectId}
GET /logs/llm/{projectId}
```

## 15. Definition of Done

A milestone is done only when:

- Code is committed in the expected module.
- APIs are documented in OpenAPI.
- Database migrations are included.
- Unit or integration tests cover the main behavior.
- Local run instructions are updated.
- Failure behavior is logged and returns structured errors.
- No LLM call occurs without an `llm_logs` record.
- No workflow node completes without a checkpoint.

## 16. Key Engineering Decisions

1. Use Chroma locally for Phase 1 RAG to reduce infrastructure friction.
2. Keep dependency mapping hardcoded in code until regeneration behavior stabilizes.
3. Use MySQL for durable audit logs and checkpoints.
4. Keep LLM retrieval centralized in Context Builder.
5. Build one vertical slice before implementing every agent.
6. Treat HITL as a persisted workflow state, not an in-memory pause.

