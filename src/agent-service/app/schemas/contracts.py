from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class StartWorkflowRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    input: str

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
    artifact_type: str = Field(alias="artifactType")
    section_name: str = Field(alias="sectionName")
    content: Any

    model_config = {"populate_by_name": True}


class SectionsResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    sections: list[SectionResponse]

    model_config = {"populate_by_name": True}
