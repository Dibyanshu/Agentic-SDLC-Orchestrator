# High Level Design (HLD)
**Product Name:** Agentic SDLC Orchestrator (Phase 1)

---

## 1. Overview

This system is a graph-driven orchestration platform that automates early SDLC stages (PRD → BA → Architecture) using AI agents, with strict human control, section-wise regeneration, controlled RAG, and cost optimization.

The system is built around a deterministic workflow engine using LangGraph, where:
- Nodes represent execution steps
- State is persisted and checkpointed
- Human input controls progression

---

## 2. System Architecture

### 2.1 Logical Architecture
Frontend (React)
→
.NET API (Orchestration Layer)
→
LangGraph Engine (Python)
→
Agent Nodes + Context Builder
→
LLM Providers + Vector DB + Graph DB
→
MySQL (State, Artifacts, Logs)


---

### 2.2 Responsibilities by Layer

#### Frontend
- Display artifacts (PRD, BA, Architecture)
- Provide HITL interface (approve, edit, regenerate)
- Show version history and logs

---

#### .NET API (Control Plane)
- Project management
- Workflow initiation
- HITL routing
- Section editing APIs
- Dependency resolution trigger
- Communication with LangGraph service

---

#### LangGraph Engine (Python)
- Executes workflow graph
- Maintains state transitions
- Handles checkpointing
- Invokes agent nodes
- Supports partial graph re-execution

---

#### Agent Engine
- Executes PM, BA, Architect agents
- Applies prompt templates
- Receives controlled context
- Returns structured outputs

---

#### Context Builder (Critical Component)
- Retrieves RAG data
- Filters and ranks relevance
- Deduplicates context
- Enforces token limits
- Constructs final prompt payload

---

#### Storage Layer
- MySQL: structured data, logs, checkpoints
- Vector DB: embeddings and semantic search
- Graph DB (optional): dependency relationships

---

## 3. LangGraph Design

### 3.1 Graph Structure
START
→
manager_node
→
pm_node
→
hitl_node
→
ba_node
→
hitl_node
→
architect_node
→
hitl_node
→
END


---

### 3.2 Node Definitions

#### manager_node
- Determines next node
- Handles regeneration routing
- Applies dependency rules
- Updates graph execution path

---

#### pm_node
- Generates PRD sections
- Uses controlled context
- Outputs structured PRD sections

---

#### ba_node
- Generates user stories and acceptance criteria
- Maintains traceability to PRD

---

#### architect_node
- Generates APIs and DB schema
- Ensures consistency with BA outputs

---

#### hitl_node
- Pauses execution
- Captures user input
- Supports:
  - Approve
  - Edit section
  - Regenerate
  - Cascade decision

---

### 3.3 Graph State Model
{
"project_id": "string",
"current_node": "string",
"artifacts": {
"PRD": {...},
"BA": {...},
"ARCH": {...}
},
"updated_section": "string",
"regeneration_mode": "none | single | cascade",
"context_cache": [],
"execution_history": []
}


---

### 3.4 Checkpointing

- State saved after each node execution
- Stored in MySQL
- Supports:
  - Resume execution
  - Debugging
  - Audit trail

---

## 4. Section-wise Regeneration Design

### 4.1 Flow
User edits section
→
HITL node captures change
→
Manager node evaluates dependencies
→
Regeneration planner creates execution path
→
LangGraph executes partial graph


---

### 4.2 Regeneration Modes

#### Single Section
- Only selected section updated
- No downstream impact

---

#### Cascade Mode
- Dependent sections identified
- Downstream nodes re-executed

---

### 4.3 Dependency Mapping (Phase 1)
PRD.Features → BA.User Stories
BA.User Stories → ARCH.APIs
ARCH.APIs → ARCH.DB Schema


---

## 5. Context Builder Design

### 5.1 Inputs

- Target section
- Artifact summary
- RAG chunks
- Constraints

---

### 5.2 Processing Steps

1. Retrieve top-K chunks (≤ 3–5)
2. Filter by relevance and tags
3. Deduplicate overlapping content
4. Compress context if needed
5. Enforce token budget

---

### 5.3 Output
```JSON
{
"system_prompt": "...",
"user_prompt": "...",
"context_payload": {
"rag_chunks": [],
"summary": "...",
"constraints": []
}
}
```

---

## 6. RAG System Design

### 6.1 Ingestion Pipeline
Upload → Parse → Chunk → Embed → Store

---

### 6.2 Supported Inputs

- Documents (PDF, DOCX, TXT)
- UI screenshots (OCR-based extraction)

---

### 6.3 Retrieval Strategy

- Top-K similarity search
- Tag-based filtering
- Stage-aware retrieval

---

### 6.4 Constraints

- Max chunks: 3–5
- No agent-driven retrieval
- Context injected centrally

---

## 7. Data Storage Design

### 7.1 MySQL

Stores:
- Projects
- Artifacts
- Sections
- Versions
- Refinement logs
- Checkpoints
- LLM logs

---

### 7.2 Vector Database

- Stores embeddings
- Supports semantic search

---

### 7.3 Graph Database (Optional)

- Stores section dependencies
- Enables impact analysis

---

## 8. LLM Interaction Design

### 8.1 Flow
Agent Node Trigger
→
Context Builder prepares input
→
LLM Call
→
Log interaction (LLM_Logs)
→
Return structured output


---

### 8.2 Prompt Structure

- System prompt (agent persona)
- User prompt (task instruction)
- Context payload (RAG + summary + constraints)

---

## 9. LLM Logging Architecture

### 9.1 Logging Trigger

- Every LLM call must generate a log entry
- Logged synchronously after response

---

### 9.2 Data Captured

- Prompt inputs
- Context payload
- Response output
- Token usage
- Latency
- Model details
- Cache usage

---

### 9.3 Storage

- Stored in MySQL (LLM_Logs table)
- Linked to:
  - project
  - artifact
  - section
  - node

---

## 10. Cost Optimization Design

### 10.1 Controls

- Token caps per node
- Context size limits
- Max refinement loops
- Response caching

---

### 10.2 Strategies

- Section-only regeneration
- Context deduplication
- Summarized context usage
- Tiered model selection

---

## 11. Error Handling and Recovery

### 11.1 Node Failure

- Retry node execution
- Log error details
- Allow manual override

---

### 11.2 Workflow Recovery

- Resume from checkpoint
- Rollback to previous version

---

### 11.3 LLM Failure

- Capture error in logs
- Retry with fallback model (optional)

---

## 12. Security and Access Control

- Role-based access (future phase)
- Secure API endpoints
- Data isolation per project

---

## 13. Scalability Considerations

- Stateless API layer
- Horizontal scaling of agent service
- Async execution support (future)
- Efficient indexing for logs and sections

---

## 14. Performance Considerations

- Limit context size
- Optimize DB queries with indexing
- Cache repeated LLM responses
- Minimize unnecessary graph execution

---

## 15. Deployment Architecture

### 15.1 Local Development

- Docker Compose:
  - MySQL
  - Vector DB
  - Graph DB (optional)
  - Python service
  - .NET API

---

### 15.2 Production (Future)

- Containerized services
- Managed DB services
- Scalable API layer

---

## 16. Future Enhancements

- Knowledge graph-driven dependency mapping
- Critic agent for validation
- Parallel node execution
- Advanced RAG ranking
- Cross-project learning

---