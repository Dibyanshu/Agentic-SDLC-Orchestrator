# Product Requirement Document (PRD)
**Product Name:** Agentic SDLC Orchestrator (Phase 1)

---

## 1. Product Vision

Build a graph-driven system that automates early SDLC stages by transforming raw inputs (ideas, documents, UI screenshots) into structured outputs (PRD, User Stories, Architecture), while maintaining strict human control, traceability, and cost efficiency.

---

## 2. Objectives

1. Automate PRD, BA, and Architecture generation using agent-based workflows.  
2. Enable section-wise refinement with controlled regeneration.  
3. Maintain full auditability through versioning and checkpoints.  
4. Integrate contextual knowledge using controlled RAG.  
5. Ensure predictable and optimized token usage.

---

## 3. Target Users

- Solution Architects  
- Product Owners  
- Lead Developers  

---

## 4. Core Principles

### 4.1 Deterministic Orchestration
Workflow execution is controlled by a graph-based state machine, not by agent decisions.

### 4.2 Section-Centric Artifacts
All outputs are divided into sections and stored independently.

### 4.3 Human-in-the-Loop Control
Every stage pauses for user approval or refinement.

### 4.4 Controlled Context Injection
Context is centrally managed and injected into agents, not dynamically fetched by them.

### 4.5 Cost Discipline
Token usage is bounded through strict limits, caching, and selective regeneration.

---

## 5. Scope (Phase 1)

### In Scope
- LangGraph-based workflow orchestration  
- PM, BA, and Architect agents  
- HITL checkpoints after each stage  
- Section-wise regeneration  
- Manual dependency mapping  
- Basic RAG (document + UI ingestion)  
- Versioning and checkpointing  
- Cost control mechanisms  

### Out of Scope
- Automatic dependency discovery  
- Multi-agent parallel execution  
- Cross-project learning  

---

## 6. Functional Requirements

### 6.1 Workflow Execution
- System initializes a project from user input.  
- Executes nodes in sequence:
  - PM Agent → PRD  
  - BA Agent → User Stories  
  - Architect Agent → APIs and DB schema  
- Execution is managed via LangGraph.

---

### 6.2 Human-in-the-Loop (HITL)
At each stage:

User can:
- Approve output  
- Edit a section  
- Request regeneration  

System must:
- Pause execution  
- Capture user input  
- Route next action via orchestrator  

---

### 6.3 Section Management

Artifacts must be stored as independent sections.

#### PRD Sections
- Overview  
- Features  
- User Flow  

#### BA Sections
- User Stories  
- Acceptance Criteria  

#### Architecture Sections
- APIs  
- DB Schema  
- HLD
- LLD

Each section must:
- Have version tracking  
- Be independently editable  
- Support partial regeneration  

---

### 6.4 Section-wise Regeneration

When a section is modified:

1. System identifies affected sections using predefined dependencies.  
2. User chooses:
   - Update only selected section  
   - Cascade update  
3. System regenerates only required sections.  

---

### 6.5 Dependency Mapping

Initial dependency rules:

- PRD.Features → BA.User Stories  
- BA.User Stories → Architecture APIs  
- Architecture APIs → DB Schema  

---

### 6.6 Controlled RAG

#### Input Sources:
- Documents (PDF, DOCX, TXT)  
- UI screenshots (via OCR)  

#### Processing:
- Chunking  
- Embedding  
- Storage in vector database  

#### Retrieval:
- Top-K relevant chunks (max 3–5)  
- Filtered by tags and stage  

#### Injection:
- Context is added to agent prompts centrally  
- Agents cannot trigger retrieval directly  

---

### 6.7 Versioning and Auditability

- Every section update creates a new version  
- All user inputs are logged  
- Full history of changes is preserved  

---

### 6.8 Checkpointing

- Workflow state is saved after each node  
- System can resume from last checkpoint  
- Checkpoints include:
  - Current node  
  - Artifact state  
  - Context cache  

---

### 6.9 Cost Control

- Token limit enforced per agent  
- Context size capped  
- Max refinement loops per stage (e.g., 2)  
- Output caching enabled  
- Tiered model usage  

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Each agent response should complete within 10 seconds  

### 7.2 Scalability
- Support at least 1,000 workflows per month  

### 7.3 Reliability
- Resume execution from any checkpoint  
- Retry failed nodes  

### 7.4 Maintainability
- Modular agent design  
- Clear separation between orchestration and execution  

### 7.5 Cost
- Target cost per workflow: ≤ $0.10  

---

## 8. System Components

### 8.1 Orchestrator (LangGraph)
- Controls workflow execution  
- Handles routing and state transitions  
- Manages regeneration logic  

---

### 8.2 Agent Engine
- Executes PM, BA, and Architect agents  
- Uses predefined prompts  
- Receives controlled context  

---

### 8.3 Context Builder
- Fetches relevant RAG data  
- Deduplicates and filters  
- Enforces token limits  
- Prepares prompt input  

---

### 8.4 Data Storage
Relational database stores:
- Projects  
- Artifacts  
- Sections  
- Versions  
- Refinement logs  
- Checkpoints  

---

### 8.5 Vector Database
- Stores embedded knowledge chunks  
- Supports similarity search  

---

### 8.6 Graph Database (Optional Phase 1 Extension)
- Stores section dependencies  
- Enables impact analysis for regeneration  

---

## 9. Data Model

### 9.1 Projects
- id  
- name  
- goal  
- created_at  

---

### 9.2 Artifacts
- id  
- project_id  
- type (PRD / BA / ARCH)  

---

### 9.3 Sections
- id  
- artifact_id  
- section_name  
- content  
- version  
- created_at  

---

### 9.4 Refinement Logs
- id  
- section_id  
- user_input  
- action_type (edit / regenerate / cascade)  
- created_at  

---

### 9.5 Checkpoints
- id  
- project_id  
- graph_state (serialized LangGraph state)  
- current_node  
- status  
- created_at  

---

### 9.6 LLM Logs (Critical)

#### Purpose
Capture full observability of LLM interactions for debugging, cost tracking, and optimization.

---

#### LLM_Logs

- id  
- project_id  
- artifact_id (nullable)  
- section_id (nullable)  
- node_name (pm_node / ba_node / architect_node)  
- agent_name (PM / BA / Architect)  

---

#### Request Details
- model_name  
- prompt_template_version  
- system_prompt  
- user_prompt  
- context_payload (JSON)  

---

#### Response Details
- response_text  
- response_format (json / text)  
- status (success / failure)  
- error_message (nullable)  

---

#### Token and Cost Tracking
- input_tokens  
- output_tokens  
- total_tokens  
- estimated_cost  

---

#### Performance Metrics
- start_time  
- end_time  
- latency_ms  

---

#### Caching Info
- cache_hit (boolean)  
- cache_key (nullable)  

---

#### Metadata
- created_at  

---

### 9.7 LLM Context Chunks

- id  
- llm_log_id  
- chunk_id  
- relevance_score  
- source_type (document / ui / note)  

---

## 10. Success Metrics

- Average cost per workflow  
- Average number of refinement iterations  
- Time to generate complete artifact set  
- User approval rate without rework  
- System uptime and reliability  

---

## 11. Risks and Mitigations

### Risk: Inconsistent outputs across sections  
Mitigation: Provide summarized global context during regeneration  

---

### Risk: Cost escalation due to repeated calls  
Mitigation: Enforce token limits, caching, and section-level updates  

---

### Risk: Incorrect dependency mapping  
Mitigation: Start with simple rules and refine incrementally  

---

### Risk: Context overload  
Mitigation: Limit RAG retrieval to top-K relevant chunks  

---

## 12. Future Enhancements

- Automated dependency detection using knowledge graph  
- Advanced RAG ranking and summarization  
- Parallel agent execution  
- Critic/validation agent  
- Cross-project knowledge reuse  

--- 