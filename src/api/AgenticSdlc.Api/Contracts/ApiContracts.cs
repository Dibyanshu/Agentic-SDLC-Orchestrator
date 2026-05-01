namespace AgenticSdlc.Api.Contracts;

public sealed record HealthResponse(string Status, string Service);

public sealed record ErrorResponse(string Code, string Message);

public sealed record CreateProjectRequest(string Name, string Goal);

public sealed record ProjectResponse(string Id, string Name, string Goal, DateTimeOffset CreatedAt);

public sealed record StartWorkflowRequest(string ProjectId, string Input);

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

