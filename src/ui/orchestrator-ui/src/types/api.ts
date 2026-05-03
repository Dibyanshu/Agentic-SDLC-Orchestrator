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
  contextPayload?: {
    rag_chunks?: Array<{
      chunk_id?: string;
      file_name?: string;
      source_type?: string;
      relevance_score?: number;
    }>;
  };
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
  sourceType: "txt" | "pdf" | "docx";
  contentHash: string;
  chunkCount: number;
  createdAt: string;
};

export type LlmProvider = "stub" | "openai" | "gemini" | "claude";

export type LlmProviderInfo = {
  provider: LlmProvider;
  defaultModel: string;
  apiKeyConfigured: boolean;
};

export type AgentLlmSettings = {
  provider: LlmProvider;
  model: string;
  tokenBudget: number;
};

export type ProjectLlmSettings = {
  projectId: string;
  agents: Record<"pm" | "ba" | "architect", AgentLlmSettings>;
};
