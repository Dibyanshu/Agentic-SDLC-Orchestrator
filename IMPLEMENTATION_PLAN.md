# Agentic SDLC Orchestrator - Executable Implementation Plan

## 0. Current Repository State

Last updated: 2026-05-03

The repository now contains a runnable Phase 1 scaffold and several executable vertical slices:

- `PRD.md`
- `HLD.md`
- `LLD.md`
- `Feature.md`
- `README.md`
- `.NET 8 API` in `src/api/AgenticSdlc.Api`
- Python FastAPI agent service in `src/agent-service`
- React/Vite UI in `src/ui/orchestrator-ui`
- MySQL migrations in `infra/mysql/migrations`
- Docker Compose runtime in `infra/docker-compose.yml`

Completed implementation:

- Docker runtime for API, agent service, MySQL, and Chroma.
- API and agent health endpoints.
- MySQL-backed project creation and lookup.
- Workflow start, resume, and status through the API.
- Deterministic stub workflow: PRD -> HITL -> BA -> HITL -> Architecture -> HITL -> completed.
- MySQL-backed artifacts, sections, section versions, checkpoints, and refinement logs.
- Section list, detail, update, and version-history APIs.
- HITL approve/edit/regenerate path with persisted refinement logs.
- Hardcoded dependency resolver and regeneration planner.
- Checkpoint retrieval endpoint.
- PM generation LLM logging endpoint.
- Multi-provider LLM client with default stub mode and OpenAI, Gemini, and Claude adapters.
- Workflow metrics endpoint for tokens, cost, cache hits, latency, LLM calls, and refinement count.
- `.env` is used for local runtime secrets and is ignored by git.
- React UI console for project creation, workflow start/resume, section editing/history, HITL actions, agent progress, logs, and metrics.
- Docker Compose UI service on `http://localhost:5173`.
- Controlled TXT/PDF/DOCX RAG vertical slice with source metadata in MySQL, chunk storage/retrieval in Chroma, context injection, and `llm_context_chunks` traces.
- Initial automated tests and Docker smoke script for the current happy path.
- Cost controls with per-node input token budgets and MySQL-backed LLM response caching.
- Per-project PM/BA/Architect LLM settings for provider, model, and input token budget.
- Intentional OpenAI and Gemini PM validation scripts with cache-aware real-provider smoke coverage.

Still pending:

- Real LLM client execution validated intentionally for Claude.
- RAG support for screenshots/OCR, delete source, and advanced ranking.

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
  ui/
    orchestrator-ui/
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

Note: broader integration tests, shared contracts, and docs folders are still pending.

## 2. Milestone Execution Order

### Milestone 1 - Repository and Local Runtime Scaffold

Status: Mostly complete.

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
   - `ui`
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

- Done: `docker compose --env-file .env -f infra/docker-compose.yml up -d --build api agent-service` starts API, agent service, MySQL, and Chroma.
- Done: `docker compose --env-file .env -f infra/docker-compose.yml up -d --build api agent-service ui` starts the React UI with API and agent service.
- Done: `.NET API` exposes `GET /health`.
- Done: `Python Agent Service` exposes `GET /health`.
- Done: React UI exposes `GET http://localhost:5173`.
- Done: README contains first-run instructions using `.env`.
- Done: create dedicated `.NET` API contract test project.
- Done: create Python unit test folder for agent-service logic.

## 3. Milestone 2 - Database Foundation

Status: Mostly complete.

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

- Done: Fresh database can be created from migrations.
- Done: `POST /projects` persists a project.
- Done: `GET /projects/{id}` returns the created project.
- Done: Section updates create a new `section_versions` row.
- Done: Checkpoints and refinement logs are persisted.
- Done: LLM logging writes exist for PM, BA, Architect, and node-based regeneration calls.
- Done: LLM context chunk writes for retrieved RAG chunks.

## 4. Milestone 3 - .NET Control Plane API

Status: Partially complete.

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
PUT  /sections/{projectId}/{artifactType}/{sectionName}
GET  /sections/{projectId}/{artifactType}/{sectionName}/versions

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

- Done: Project, workflow start/status, sections, section detail, section update, section versions, HITL action, and checkpoints endpoints exist.
- Done: Invalid HITL actions fail with `400`.
- Done: API can call the agent service.
- Done: `POST /workflow/resume`.
- Done: `GET /logs/llm/{projectId}`.
- Partial: automated API contract tests exist; live project, RAG, HITL, metrics, and checkpoint path is covered by Docker smoke script.
- Pending: normalize all downstream agent-service errors into structured API errors instead of relying on `EnsureSuccessStatusCode`.

## 5. Milestone 4 - Python Agent Service Skeleton

Status: Partially complete.

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
GET  /sections/{projectId}
GET  /sections/{projectId}/{artifactType}/{sectionName}
PUT  /sections/{projectId}/{artifactType}/{sectionName}
GET  /sections/{projectId}/{artifactType}/{sectionName}/versions
GET  /checkpoints/{projectId}
GET  /health
```

Acceptance criteria:

- Done: Agent service can initialize an `AgentState`.
- Done: `manager_node -> pm_node -> hitl_node` executes and pauses.
- Done: Checkpoint is saved after node transitions.
- Done: sections, versions, checkpoints, and HITL refinement logs are persisted.
- Pending: replace manual runner with compiled LangGraph graph if strict LangGraph execution is required for the demo.
- Done: `POST /workflow/resume`.

## 6. Milestone 5 - First Vertical Slice: Project to PRD to HITL

Status: Partially complete with deterministic stub output.

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

- Done: A project can generate PRD sections through deterministic PM stub logic.
- Done: Workflow status reports `paused_for_hitl`.
- Done: PRD sections are persisted and can be queried.
- Partial: PM prompt template execution is multi-provider ready and defaults to deterministic stub mode.
- Done: invalid PM JSON/failure attempts are logged and retried up to 2 times after the first attempt.
- Done: PM LLM log includes prompt, response, token estimates, status, latency, and cache metadata.
- Partial: OpenAI and Gemini PM modes validated with real provider calls; Claude still pending real-provider validation.

## 7. Milestone 6 - HITL Approve/Edit/Regenerate

Status: Partially complete.

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

- Done: Approving PRD moves workflow to BA stage.
- Done: Editing `PRD.Features` creates a new version.
- Done: Regeneration creates a plan and reruns the selected deterministic node sequence.
- Done: refinement actions are persisted in `refinement_logs`.
- Done: max refinement loop enforcement for edit/regenerate actions.
- Done: regeneration reruns nodes through the same LLM logging path.
- Pending: validate regeneration through real provider calls.

## 8. Milestone 7 - BA and Architect Agents

Status: Partially complete with deterministic stub output.

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

- Done: Full workflow can run from project input to PRD, BA, and Architecture artifacts.
- Done: Workflow pauses after each stage.
- Done: Approving all stages marks workflow as `completed`.
- Partial: BA and Architect prompt templates are multi-provider ready and default to deterministic stub mode.
- Pending: stricter structured output validation.

## 9. Milestone 8 - Section-wise Regeneration

Status: Partially complete.

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

- Done: `single` mode plans the owning node.
- Done: `cascade` mode plans downstream nodes.
- Done: unchanged section content does not create noisy section versions.
- Pending: limit regeneration writes to exact dependent sections rather than whole owning artifact output where needed.
- Pending: make regeneration plan visible in the API workflow status response explicitly.

## 10. Milestone 9 - Controlled RAG

Status: Partially complete with TXT, PDF, and DOCX ingestion.

Goal: support document and screenshot context without giving agents direct retrieval control.

Endpoints:

```text
POST /rag/sources
GET  /rag/sources/{projectId}
DELETE /rag/sources/{sourceId}
```

Tasks:

1. Done: Add JSON TXT/PDF/DOCX upload handling in `.NET API`.
2. Done: Add TXT/PDF/DOCX ingestion endpoint in Python Agent Service.
3. Implement parsers:
   - Done: TXT first
   - Done: PDF second
   - Done: DOCX third
   - Pending: OCR screenshot last
4. Done: Chunk parsed text.
5. Done: Generate deterministic local embeddings for parsed source chunks.
6. Done: Store chunks in Chroma with project and source tags.
7. Done: Retrieve top 5, filter to top 3 in Context Builder.
8. Pending: deduplicate chunks before prompt construction.
9. Pending: delete source and remove related Chroma chunks.

Acceptance criteria:

- Done: Uploaded TXT, PDF, and DOCX documents can be parsed, chunked, and indexed for workflow context.
- Done: Uploaded TXT document can influence PRD generation through the Docker smoke path.
- Done: Context Builder returns at most 3 chunks.
- Done: LLM logs record which chunks were injected through `llm_context_chunks`.
- Agents do not call retrieval directly.

## 11. Milestone 10 - Cost Controls and Observability

Goal: make usage measurable and bounded.

Tasks:

1. Done: Enforce configurable input token budgets:
   - PM: `3000`
   - BA: `3000`
   - Architect: `4000`
2. Add context truncation/summarization guard.
3. Done: Add MySQL-backed response cache table.
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

Status:

- Done: `GET /metrics/workflow/{projectId}` exposes token totals, estimated cost, latency per node, cache hits, LLM call count, and refinement count.
- Done: token budget enforcement.
- Done: response caching.
- Pending: context truncation/summarization guard.

Acceptance criteria:

- Done: Token budget violations fail before LLM call.
- Done: Repeated identical prompt/context returns cached response.
- Done: Project-level metrics can be queried.

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
- Done: one command runs `.NET` API tests with `dotnet test AgenticSdlc.sln`.
- Done: one command runs Python unit tests with `python -m unittest discover -s src/agent-service/tests`.
- Done: Docker smoke script exercises project creation, TXT RAG upload, workflow generation, HITL approvals, logs, metrics, and checkpoints.
- Done: Python tests cover TXT, PDF, and DOCX parsing.
- Done: OpenAI validation script exercises PM-only real-provider generation and cache hit behavior.
- Done: Gemini validation script exercises PM-only real-provider generation and cache hit behavior.
- Failed LLM calls are visible in logs.
- Checkpoint resume works after service restart.

## 13. Implementation Backlog

### P0 - Must Have for Phase 1 Demo

- Done: Repo scaffold
- Done: Docker Compose with MySQL and Chroma
- Done: Project API
- Done: Section API with versioning
- Done: Workflow start/resume.
- Partial: LangGraph skeleton. Deterministic runner exists; compiled LangGraph graph is pending if required.
- Partial: PM, BA, Architect nodes. Deterministic stubs exist; OpenAI and Gemini PM validation pass; full real-provider workflow validation is pending.
- Done: HITL approve/edit/regenerate with loop limit enforcement.
- Done: LLM logging for PM, BA, Architect, and node-based regeneration.
- Done: Checkpointing
- Partial: Hardcoded dependency-based regeneration. Planner exists; exact dependent-section write behavior needs refinement.

### P1 - Should Have

- Partial: TXT/PDF/DOCX ingestion implemented; OCR screenshot ingestion pending
- Done: Chroma retrieval
- Done: Token budget enforcement
- Done: Response caching
- Done: Metrics endpoint
- Done: UI frontend
- Done: End-to-end Docker smoke script
- Done: OpenAI PM validation script
- Done: Gemini PM validation script

### P2 - Later

- OCR screenshots
- Neo4j dependency graph
- JWT/RBAC
- Redis cache
- Advanced RAG ranking
- Critic/validation agent

## 14. Recommended First Sprint

Status: Completed as an initial vertical slice, with deterministic stub agents.

Sprint length: 1 week.

Deliverable: first vertical slice from project creation to PRD generation and HITL pause.

Day-by-day plan:

1. Day 1: scaffold `.NET API`, Python Agent Service, Docker Compose, README.
2. Day 2: database migrations and project/section persistence.
3. Day 3: Python LangGraph skeleton and checkpoint save.
4. Day 4: PM agent, prompt template, LLM client, LLM logging.
5. Day 5: wire `.NET API` to agent service, run start workflow, verify PRD sections.

## 14.1 Recommended Next Sprint

Sprint length: 1 week.

Deliverable: complete PM LLM slice with mandatory LLM logging and controlled retry behavior.

Day-by-day plan:

1. Done: implement `llm_logs` write service in Python and expose API log retrieval through `.NET`.
2. Done: implement multi-provider LLM client using provider keys from `.env`, with deterministic stub default.
3. Done: implement PM prompt template, JSON parsing, schema validation, and retry up to 2 times.
4. Done: wire PM node to LLM client and store LLM logs for success and failure.
5. Done: validate `POST /projects -> POST /workflow/start -> GET /sections -> GET /logs/llm` in Docker using stub mode.
6. Partial: validate OpenAI, Gemini, and Claude modes intentionally with real provider keys. OpenAI and Gemini PM validation are done; Claude is pending.
7. Done: extend the same LLM logging pattern to BA, Architect, and regeneration.
8. Pending: validate regeneration intentionally with real provider keys.

Next sprint demo script:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d --build api agent-service
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

- Code exists in the expected module.
- APIs are documented in OpenAPI.
- Database migrations are included.
- Unit or integration tests cover the main behavior.
- Local run instructions are updated.
- Failure behavior is logged and returns structured errors.
- No LLM call occurs without an `llm_logs` record.
- No workflow node completes without a checkpoint.

For this local working session, a milestone should also be validated with:

- `python -m compileall src/agent-service/app`
- `& 'C:\Program Files\dotnet\dotnet.exe' build src/api/AgenticSdlc.Api/AgenticSdlc.Api.csproj`
- `dotnet test AgenticSdlc.sln`
- `python -m unittest discover -s src/agent-service/tests`
- `docker compose --env-file .env -f infra/docker-compose.yml up -d --build api agent-service`
- `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/validate-openai.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/validate-gemini.ps1`

## 16. Key Engineering Decisions

1. Use Chroma locally for Phase 1 RAG to reduce infrastructure friction.
2. Keep dependency mapping hardcoded in code until regeneration behavior stabilizes.
3. Use MySQL for durable audit logs and checkpoints.
4. Keep LLM retrieval centralized in Context Builder.
5. Build one vertical slice before implementing every agent.
6. Treat HITL as a persisted workflow state, not an in-memory pause.
7. Use `.env` for local secrets and keep `.env.example` as the committed template.
8. Avoid creating new section versions when regenerated content is unchanged.
