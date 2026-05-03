export type ArtifactType = "PRD" | "BA" | "ARCH";

export type Project = {
  id: string;
  name: string;
  goal: string;
  createdAt: string;
};

export type WorkflowResponse = {
  projectId: string;
  status: string;
  currentNode: string;
  artifacts: Record<string, Record<string, string>>;
};

export type Section = {
  id?: string;
  artifactType: ArtifactType;
  sectionName: string;
  version?: number;
  content: string;
};

export type SectionVersion = {
  id: number;
  sectionId: string;
  version: number;
  content: string;
  changeReason?: string;
  createdAt: string;
};

export type LlmLog = {
  id: number;
  nodeName: string;
  agentName: string;
  modelName: string;
  status: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  latencyMs: number;
  systemPrompt: string;
  userPrompt: string;
  responseText?: string;
  createdAt: string;
};

export type WorkflowMetrics = {
  projectId: string;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalTokens: number;
  estimatedCost: string;
  cacheHitCount: number;
  llmCallCount: number;
  refinementCount: number;
  latencyByNode: Array<{
    nodeName: string;
    callCount: number;
    totalLatencyMs: number;
    averageLatencyMs: number;
  }>;
};

export type RagSource = {
  id: string;
  projectId: string;
  fileName: string;
  sourceType: string;
  contentHash: string;
  chunkCount: number;
  createdAt: string;
};
