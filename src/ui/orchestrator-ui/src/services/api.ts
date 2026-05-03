import axios from "axios";
import type {
  ArtifactType,
  LlmLog,
  Project,
  RagSource,
  Section,
  SectionVersion,
  WorkflowMetrics,
  WorkflowResponse,
} from "../types/api";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080",
});

export async function createProject(name: string, goal: string): Promise<Project> {
  const response = await client.post<Project>("/projects", { name, goal });
  return response.data;
}

export async function startWorkflow(projectId: string, input: string): Promise<WorkflowResponse> {
  const response = await client.post<WorkflowResponse>("/workflow/start", { projectId, input });
  return response.data;
}

export async function resumeWorkflow(projectId: string): Promise<WorkflowResponse> {
  const response = await client.post<WorkflowResponse>("/workflow/resume", { projectId });
  return response.data;
}

export async function getWorkflowStatus(projectId: string): Promise<WorkflowResponse> {
  const response = await client.get<WorkflowResponse>(`/workflow/${projectId}/status`);
  return response.data;
}

export async function getSections(projectId: string): Promise<Section[]> {
  const response = await client.get<{ sections: Section[] }>(`/sections/${projectId}`);
  return response.data.sections;
}

export async function updateSection(
  projectId: string,
  artifactType: ArtifactType,
  sectionName: string,
  content: string,
): Promise<Section> {
  const response = await client.put<Section>(
    `/sections/${projectId}/${artifactType}/${encodeURIComponent(sectionName)}`,
    { content },
  );
  return response.data;
}

export async function getSectionVersions(
  projectId: string,
  artifactType: ArtifactType,
  sectionName: string,
): Promise<SectionVersion[]> {
  const response = await client.get<{ versions: SectionVersion[] }>(
    `/sections/${projectId}/${artifactType}/${encodeURIComponent(sectionName)}/versions`,
  );
  return response.data.versions;
}

export async function hitlAction(payload: {
  projectId: string;
  action: "approve" | "edit" | "regenerate";
  section?: string;
  content?: string;
  mode?: "single" | "cascade";
}): Promise<WorkflowResponse> {
  const response = await client.post<WorkflowResponse>("/hitl/action", payload);
  return response.data;
}

export async function getLogs(projectId: string): Promise<LlmLog[]> {
  const response = await client.get<{ logs: LlmLog[] }>(`/logs/llm/${projectId}`);
  return response.data.logs;
}

export async function getMetrics(projectId: string): Promise<WorkflowMetrics> {
  const response = await client.get<WorkflowMetrics>(`/metrics/workflow/${projectId}`);
  return response.data;
}

export async function uploadRagSource(projectId: string, fileName: string, content: string): Promise<RagSource> {
  const response = await client.post<RagSource>("/rag/sources", {
    projectId,
    fileName,
    content,
    sourceType: "txt",
  });
  return response.data;
}

export async function getRagSources(projectId: string): Promise<RagSource[]> {
  const response = await client.get<{ sources: RagSource[] }>(`/rag/sources/${projectId}`);
  return response.data.sources;
}
