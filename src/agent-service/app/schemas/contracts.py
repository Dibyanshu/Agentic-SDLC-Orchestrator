from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class StartWorkflowRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    input: str

    model_config = {"populate_by_name": True}


class ResumeWorkflowRequest(BaseModel):
    project_id: str = Field(alias="projectId")

    model_config = {"populate_by_name": True}


class HitlActionRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    action: str
    section: str | None = None
    content: str | None = None
    mode: str | None = None

    model_config = {"populate_by_name": True}


class WorkflowResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    status: str
    current_node: str = Field(alias="currentNode")
    artifacts: dict[str, Any]

    model_config = {"populate_by_name": True}


class SectionResponse(BaseModel):
    id: str | None = None
    artifact_type: str = Field(alias="artifactType")
    section_name: str = Field(alias="sectionName")
    version: int | None = None
    content: Any

    model_config = {"populate_by_name": True}


class SectionsResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    sections: list[SectionResponse]

    model_config = {"populate_by_name": True}


class UpdateSectionRequest(BaseModel):
    content: Any


class SectionVersionResponse(BaseModel):
    id: int
    section_id: str = Field(alias="sectionId")
    version: int
    content: Any
    change_reason: str | None = Field(alias="changeReason")
    created_at: str = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class SectionVersionsResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    artifact_type: str = Field(alias="artifactType")
    section_name: str = Field(alias="sectionName")
    versions: list[SectionVersionResponse]

    model_config = {"populate_by_name": True}


class CheckpointResponse(BaseModel):
    id: int
    project_id: str = Field(alias="projectId")
    current_node: str = Field(alias="currentNode")
    status: str
    graph_state: dict[str, Any] = Field(alias="graphState")
    created_at: str = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class CheckpointsResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    checkpoints: list[CheckpointResponse]

    model_config = {"populate_by_name": True}


class LlmLogResponse(BaseModel):
    id: int
    project_id: str = Field(alias="projectId")
    artifact_id: str | None = Field(alias="artifactId")
    section_id: str | None = Field(alias="sectionId")
    node_name: str = Field(alias="nodeName")
    agent_name: str = Field(alias="agentName")
    model_name: str = Field(alias="modelName")
    prompt_template_version: str | None = Field(alias="promptTemplateVersion")
    system_prompt: str = Field(alias="systemPrompt")
    user_prompt: str = Field(alias="userPrompt")
    context_payload: dict[str, Any] = Field(alias="contextPayload")
    response_text: str | None = Field(alias="responseText")
    response_format: str = Field(alias="responseFormat")
    status: str
    error_message: str | None = Field(alias="errorMessage")
    input_tokens: int = Field(alias="inputTokens")
    output_tokens: int = Field(alias="outputTokens")
    total_tokens: int = Field(alias="totalTokens")
    estimated_cost: str = Field(alias="estimatedCost")
    latency_ms: int = Field(alias="latencyMs")
    cache_hit: bool = Field(alias="cacheHit")
    cache_key: str | None = Field(alias="cacheKey")
    start_time: str | None = Field(alias="startTime")
    end_time: str | None = Field(alias="endTime")
    created_at: str = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class LlmLogsResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    logs: list[LlmLogResponse]

    model_config = {"populate_by_name": True}


class NodeLatencyMetric(BaseModel):
    node_name: str = Field(alias="nodeName")
    call_count: int = Field(alias="callCount")
    total_latency_ms: int = Field(alias="totalLatencyMs")
    average_latency_ms: float = Field(alias="averageLatencyMs")

    model_config = {"populate_by_name": True}


class WorkflowMetricsResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    total_input_tokens: int = Field(alias="totalInputTokens")
    total_output_tokens: int = Field(alias="totalOutputTokens")
    total_tokens: int = Field(alias="totalTokens")
    estimated_cost: str = Field(alias="estimatedCost")
    cache_hit_count: int = Field(alias="cacheHitCount")
    llm_call_count: int = Field(alias="llmCallCount")
    refinement_count: int = Field(alias="refinementCount")
    latency_by_node: list[NodeLatencyMetric] = Field(alias="latencyByNode")

    model_config = {"populate_by_name": True}
