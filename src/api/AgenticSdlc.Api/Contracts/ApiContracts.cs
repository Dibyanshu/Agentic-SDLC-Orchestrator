namespace AgenticSdlc.Api.Contracts;

public sealed record HealthResponse(string Status, string Service);

public sealed record ErrorResponse(string Code, string Message);

public sealed record CreateProjectRequest(string Name, string Goal);

public sealed record ProjectResponse(string Id, string Name, string Goal, DateTimeOffset CreatedAt);

public sealed record StartWorkflowRequest(string ProjectId, string Input);

public sealed record ResumeWorkflowRequest(string ProjectId);

public sealed record HitlActionRequest(
    string ProjectId,
    string Action,
    string? Section,
    string? Content,
    string? Mode);

public sealed record WorkflowResponse(
    string ProjectId,
    string Status,
    string CurrentNode,
    IReadOnlyDictionary<string, object?> Artifacts);

public sealed record SectionResponse(
    string? Id,
    string ArtifactType,
    string SectionName,
    int? Version,
    object? Content);

public sealed record SectionsResponse(
    string ProjectId,
    IReadOnlyList<SectionResponse> Sections);

public sealed record UpdateSectionRequest(object? Content);

public sealed record SectionVersionResponse(
    long Id,
    string SectionId,
    int Version,
    object? Content,
    string? ChangeReason,
    DateTimeOffset CreatedAt);

public sealed record SectionVersionsResponse(
    string ProjectId,
    string ArtifactType,
    string SectionName,
    IReadOnlyList<SectionVersionResponse> Versions);

public sealed record CheckpointResponse(
    long Id,
    string ProjectId,
    string CurrentNode,
    string Status,
    object? GraphState,
    DateTimeOffset CreatedAt);

public sealed record CheckpointsResponse(
    string ProjectId,
    IReadOnlyList<CheckpointResponse> Checkpoints);

public sealed record LlmLogResponse(
    long Id,
    string ProjectId,
    string? ArtifactId,
    string? SectionId,
    string NodeName,
    string AgentName,
    string ModelName,
    string? PromptTemplateVersion,
    string SystemPrompt,
    string UserPrompt,
    object? ContextPayload,
    string? ResponseText,
    string ResponseFormat,
    string Status,
    string? ErrorMessage,
    int InputTokens,
    int OutputTokens,
    int TotalTokens,
    string EstimatedCost,
    int LatencyMs,
    bool CacheHit,
    string? CacheKey,
    DateTimeOffset? StartTime,
    DateTimeOffset? EndTime,
    DateTimeOffset CreatedAt);

public sealed record LlmLogsResponse(
    string ProjectId,
    IReadOnlyList<LlmLogResponse> Logs);

public sealed record NodeLatencyMetric(
    string NodeName,
    int CallCount,
    int TotalLatencyMs,
    double AverageLatencyMs);

public sealed record WorkflowMetricsResponse(
    string ProjectId,
    int TotalInputTokens,
    int TotalOutputTokens,
    int TotalTokens,
    string EstimatedCost,
    int CacheHitCount,
    int LlmCallCount,
    int RefinementCount,
    IReadOnlyList<NodeLatencyMetric> LatencyByNode);

public sealed record RagSourceCreateRequest(
    string ProjectId,
    string FileName,
    string Content,
    string SourceType);

public sealed record RagSourceResponse(
    string Id,
    string ProjectId,
    string FileName,
    string SourceType,
    string ContentHash,
    int ChunkCount,
    DateTimeOffset CreatedAt);

public sealed record RagSourcesResponse(
    string ProjectId,
    IReadOnlyList<RagSourceResponse> Sources);
