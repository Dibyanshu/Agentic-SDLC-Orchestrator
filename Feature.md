```markdown
# Feature List – Agentic SDLC Orchestrator (Phase 1)

## 1. Overview
This document defines an execution-ready feature breakdown for building a LangGraph-based agentic SDLC system.

The system must implement:
- Deterministic LangGraph workflow
- Section-wise artifact management
- HITL (Human-in-the-loop)
- Controlled RAG
- LLM logging and cost tracking

LangGraph will act as the orchestration engine where nodes define execution steps and edges define transitions. :contentReference[oaicite:0]{index=0}

---

## 2. Core Workflow Features

### 2.1 Initialize Project
**API**
POST /projects

**Input**
```json
{
"name": "string",
"goal": "string"
}
```

**Output**
```json
{
"project_id": "string"
}
```

---

### 2.2 Start Workflow
**API**
POST /workflow/start

**Input**
```json
{
"project_id": "string",
"input": "raw business requirement"
}
```

**Behavior**
- Initialize LangGraph state
- Trigger graph execution from START node
- Route to pm_node

---

## 3. LangGraph Execution Features

### 3.1 Graph Definition
Implement StateGraph with nodes:
- manager_node
- pm_node
- ba_node
- architect_node
- hitl_node

**Key requirement**
- Graph must support:
  - branching
  - looping
  - partial execution
    (LangGraph supports cyclical workflows and state transitions) :contentReference[oaicite:1]{index=1}

---

### 3.2 Graph State Structure
```json
{
project_id: string,
current_node: string,
artifacts: {
PRD: {},
BA: {},
ARCH: {}
},
updated_section: string | null,
regeneration_mode: "none | single | cascade",
context_cache: [],
execution_plan: []
}
```

---

### 3.3 Node Execution Contract
Each node must:
1. Receive state
2. Build context via Context Builder
3. Call LLM
4. Store output in Sections table
5. Log LLM interaction
6. Return updated state

---

## 4. Agent Features

### 4.1 PM Agent
**Input**
- user input
- RAG context

**Output Sections**
- Overview
- Features
- User Flow

---

### 4.2 BA Agent
**Input**
- PRD sections

**Output**
- User Stories
- Acceptance Criteria

---

### 4.3 Architect Agent
**Input**
- BA output

**Output**
- APIs
- DB Schema

---

## 5. HITL Features

### 5.1 HITL Pause
- Workflow must pause at hitl_node
- State persisted in DB
- Return response to UI

---

### 5.2 HITL Actions
**API**
POST /hitl/action

**Input**
```json
{
"project_id": "string",
"action": "approve | edit | regenerate",
"section": "PRD.Features",
"content": "optional",
"mode": "single | cascade"
}
```

---

### 5.3 HITL Logic
| Action | Behavior |
|------|--------|
| approve | move to next node |
| edit | update section |
| regenerate | trigger regeneration |

---

## 6. Section Management Features

### 6.1 Store Sections
Each artifact must be stored as:
`artifact_type + section_name`

Example:
- PRD.Features
- BA.UserStories

---

### 6.2 Section Update
**API**
PUT /sections/{id}

---

### 6.3 Versioning
- Increment version on every update
- Store previous versions

---

## 7. Section-wise Regeneration

### 7.1 Dependency Rules
Hardcode mapping:
- PRD.Features → BA.UserStories
- BA.UserStories → ARCH.APIs
- ARCH.APIs → ARCH.DB

---

### 7.2 Regeneration Flow
1. Identify updated section
2. Resolve dependencies
3. Build execution_plan
4. Re-run only required nodes

---

### 7.3 Regeneration Planner
```python
if mode == "single":
    run only current node
else:
    run all dependent nodes
```

---

## 8. Context Builder Features

### 8.1 Inputs
- target section
- artifact summary
- RAG chunks

---

### 8.2 Processing
- retrieve top 5 chunks
- filter to top 3
- deduplicate
- enforce token limit

---

### 8.3 Output
```json
{
summary: "...",
rag_chunks: [],
constraints: []
}
```

---

## 9. RAG Features

### 9.1 Ingestion
Pipeline:
Upload → Parse → Chunk → Embed → Store

---

### 9.2 Supported Inputs
- PDF
- DOCX
- TXT
- UI screenshots (OCR)

---

### 9.3 Retrieval
- similarity search
- top_k = 3–5
- stage-based filtering

---

## 10. LLM Integration Features

### 10.1 LLM Client
- Accept prompt + context
- Call provider (OpenAI / local)
- Return structured response

---

### 10.2 Prompt Structure
- system_prompt
- user_prompt
- context_payload

---

## 11. LLM Logging Features (MANDATORY)

### 11.1 Log Every Call
Create entry in LLM_Logs table

---

### 11.2 Capture Fields
- model_name
- system_prompt
- user_prompt
- context_payload
- response_text
- input_tokens
- output_tokens
- latency_ms
- status

---

### 11.3 Logging Flow
LLM Call
→ Capture start_time
→ Execute
→ Capture response
→ Store log

---

## 12. Database Features

### 12.1 Core Tables
- Projects
- Artifacts
- Sections
- Refinement_Logs
- Checkpoints
- LLM_Logs

---

### 12.2 Indexing
Create indexes:
- project_id
- section_id
- node_name
- created_at

---

## 13. Checkpointing Features

### 13.1 Save State
- After each node
- Store serialized graph state

---

### 13.2 Resume Workflow
**API**
POST /workflow/resume

---

## 14. Cost Control Features

### 14.1 Token Limits
- PM: 3000
- BA: 3000
- Architect: 4000

---

### 14.2 Context Limits
- max chunks: 3
- max tokens: enforced

---

### 14.3 Loop Control
- max refinement loops = 2

---

### 14.4 Caching
- cache key = hash(prompt + context)
- skip LLM if cache hit

---

## 15. Error Handling

### 15.1 LLM Failure
- retry 2 times
- log error

---

### 15.2 Node Failure
- rollback to last checkpoint

---

## 16. Deployment Features

### 16.1 Docker Services
- mysql
- python-agent
- dotnet-api
- vector-db

---

### 16.2 Environment Variables
```env
OPENAI_API_KEY=
DB_CONNECTION=
VECTOR_DB_URL=
```

---

## 17. Observability Features

### 17.1 Logs
- LLM logs
- workflow logs
- error logs

---

### 17.2 Metrics
- latency per node
- cost per workflow
- token usage

---

## 18. Future Extensions (Not Phase 1)
- knowledge graph integration
- critic agent
- parallel execution
- advanced RAG ranking

---

## 19. Execution Order (Recommended)
1. Setup DB schema
2. Build LangGraph skeleton
3. Implement PM agent
4. Add HITL
5. Add BA + Architect
6. Add regeneration
7. Add RAG
8. Add logging
9. Add cost controls

---

## Final Note
The system must follow:
- deterministic workflow execution
- centralized context injection
- strict state management

LangGraph enables durable execution, human-in-the-loop control, and stateful workflows, making it suitable for this architecture. :contentReference[oaicite:2]{index=2}
```