# Low Level Design (LLD)
**Product Name:** Agentic SDLC Orchestrator (Phase 1)

---

## 1. Overview

This document provides a detailed implementation-level design for the Agentic SDLC Orchestrator. It defines:
- Service structure
- Module-level design
- LangGraph implementation details
- API contracts
- Database schema
- RAG pipeline
- LLM interaction layer
- Section-wise regeneration engine

---

## 2. Technology Stack

### Backend
- .NET 8 (Web API)
- Python (FastAPI + LangGraph)

### Data
- MySQL (primary storage)
- Vector DB (Pinecone / Chroma)
- Graph DB (Neo4j - optional)

### AI
- LLM providers (GPT / Claude / Local models)
- Embedding model (OpenAI / BGE / Instructor)

---

## 3. Service Architecture

### 3.1 Services

#### 1. API Service (.NET)
- Project management
- Section management
- HITL actions
- Workflow triggers

---

#### 2. Agent Service (Python)
- LangGraph execution
- Agent nodes
- Context builder
- RAG retrieval
- LLM interaction

---

#### 3. Storage Services
- MySQL (relational data)
- Vector DB (embeddings)
- Graph DB (dependencies)

---

## 4. Module Design

### 4.1 .NET API Modules

#### ProjectController
- POST /projects
- GET /projects/{id}

---

#### WorkflowController
- POST /workflow/start
- POST /workflow/resume

---

#### SectionController
- GET /sections/{projectId}
- PUT /sections/{sectionId}

---

#### HITLController
- POST /hitl/action

---

#### LogsController
- GET /logs/llm/{projectId}

---

---

### 4.2 Python Service Modules

#### graph/
- graph_builder.py
- state_model.py
- nodes/

#### agents/
- pm_agent.py
- ba_agent.py
- architect_agent.py

#### context/
- context_builder.py
- rag_retriever.py

#### llm/
- llm_client.py
- prompt_templates.py

#### logging/
- llm_logger.py

#### regeneration/
- dependency_resolver.py
- regeneration_planner.py

---

## 5. LangGraph Implementation

### 5.1 State Model

```python
class AgentState(TypedDict):
    project_id: str
    current_node: str
    artifacts: dict
    updated_section: Optional[str]
    regeneration_mode: str
    context_cache: list
    execution_history: list

```

### 5.2 Graph Builder

```python
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("manager_node", manager_node)
    graph.add_node("pm_node", pm_node)
    graph.add_node("ba_node", ba_node)
    graph.add_node("architect_node", architect_node)
    graph.add_node("hitl_node", hitl_node)

    graph.set_entry_point("manager_node")

    graph.add_edge("manager_node", "pm_node")
    graph.add_edge("pm_node", "hitl_node")
    graph.add_edge("hitl_node", "ba_node")
    graph.add_edge("ba_node", "hitl_node")
    graph.add_edge("hitl_node", "architect_node")
    graph.add_edge("architect_node", "hitl_node")

    return graph

```

### 5.3 Node Implementation

#### manager_node
```python

def manager_node(state):
    if state.get("updated_section"):
        plan = resolve_dependencies(state["updated_section"])
        state["execution_plan"] = plan
        return {"next": plan[0]}
    
    return {"next": "pm_node"}

```
#### pm_node
```python
def pm_node(state):
    context = build_context(state, "PRD")
    response = run_llm("pm_agent", context)
    update_sections(state, "PRD", response)
    return state
```
#### hitl_node
```python
def hitl_node(state):
    return state  # execution paused externally
```
## 6. Context Builder
### 6.1 Implementation
```python
def build_context(state, stage):
    summary = summarize_artifacts(state)
    chunks = retrieve_rag_chunks(state, stage)

    context = {
        "summary": summary,
        "rag_chunks": chunks[:3],
        "constraints": []
    }

    return context
```
## 7. RAG Retriever
```python
def retrieve_rag_chunks(state, stage):
    query = generate_query(state, stage)
    results = vector_db.search(query, top_k=5)
    return filter_by_stage(results, stage)
```
## 8. LLM Client
```python
def run_llm(agent_name, context):
    prompt = build_prompt(agent_name, context)

    start = time.time()
    response = llm_api.call(prompt)
    end = time.time()

    log_llm_call(prompt, response, start, end)

    return response
```
## 9. LLM Logger
```python
def log_llm_call(prompt, response, start, end):
    log = {
        "system_prompt": prompt.system,
        "user_prompt": prompt.user,
        "response": response.text,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "latency_ms": (end - start) * 1000
    }
    save_to_db(log)
```
## 10. Dependency Resolver
```python
def resolve_dependencies(section):
    mapping = {
        "PRD.Features": ["pm_node", "ba_node", "architect_node"],
        "BA.UserStories": ["ba_node", "architect_node"],
        "ARCH.APIs": ["architect_node"]
    }
    return mapping.get(section, ["pm_node"])
```
## 11. Regeneration Planner
```python
def plan_regeneration(section, mode):
    deps = resolve_dependencies(section)

    if mode == "single":
        return [deps[0]]
    return deps
```
## 12. Database Schema (SQL)
### Projects
```sql
CREATE TABLE Projects (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(255),
  goal TEXT,
  created_at TIMESTAMP
);
```
### Artifacts
```sql
CREATE TABLE Artifacts (
  id VARCHAR(50) PRIMARY KEY,
  project_id VARCHAR(50),
  type VARCHAR(50)
);
```
### Sections
```sql
CREATE TABLE Sections (
  id VARCHAR(50) PRIMARY KEY,
  artifact_id VARCHAR(50),
  section_name VARCHAR(100),
  content JSON,
  version INT,
  created_at TIMESTAMP
);
```
### LLM Logs
```sql
CREATE TABLE LLM_Logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  project_id VARCHAR(50),
  section_id VARCHAR(50),
  node_name VARCHAR(50),
  model_name VARCHAR(50),
  system_prompt TEXT,
  user_prompt TEXT,
  response_text LONGTEXT,
  input_tokens INT,
  output_tokens INT,
  latency_ms INT,
  created_at TIMESTAMP
);
```
## 13. API Contracts
### Start Workflow
```yaml
POST /workflow/start
{
  "project_id": "123",
  "input": "Build login system"
}
```
### HITL Action
```yaml
POST /hitl/action
{
  "project_id": "123",
  "action": "edit",
  "section": "PRD.Features",
  "content": "Add OTP login",
  "mode": "cascade"
}
```
## 14. Caching
 - Key: hash(prompt + context)
 - Store response in Redis (optional)

## 15. Error Handling
 - Retry LLM calls (max 2)
 - Log failures
 - Fallback model (optional)

## 16. Security
 - Input validation
 - API authentication (JWT future)
 - Data isolation per project

## 17. Deployment
### Docker Services
 - mysql
 - vector-db
 - python-agent-service
 - dotnet-api
 
## 18. Future Extensions
### Knowledge graph automation
 - Multi-agent parallelism
 - Critic agent
 - Advanced caching