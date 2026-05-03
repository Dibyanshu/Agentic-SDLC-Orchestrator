using AgenticSdlc.Api.Contracts;
using AgenticSdlc.Api.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddCors(options =>
{
    options.AddPolicy("UiCors", policy =>
    {
        var uiOrigin = Environment.GetEnvironmentVariable("UI_ORIGIN") ?? "http://localhost:5173";
        policy.WithOrigins(uiOrigin)
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});
builder.Services.AddSingleton<IProjectStore, MySqlProjectStore>();
builder.Services.AddHttpClient<IAgentServiceClient, AgentServiceClient>((sp, client) =>
{
    var configuration = sp.GetRequiredService<IConfiguration>();
    var baseUrl = Environment.GetEnvironmentVariable("AGENT_SERVICE_URL")
        ?? configuration["AgentService:BaseUrl"]
        ?? "http://localhost:8000";

    client.BaseAddress = new Uri(baseUrl);
});

var app = builder.Build();

app.UseCors("UiCors");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapGet("/health", () => Results.Ok(new HealthResponse("ok", "api")))
    .WithName("Health");

app.MapPost("/projects", (CreateProjectRequest request, IProjectStore store) =>
{
    if (string.IsNullOrWhiteSpace(request.Name) || string.IsNullOrWhiteSpace(request.Goal))
    {
        return Results.BadRequest(new ErrorResponse("project_validation_failed", "Project name and goal are required."));
    }

    var project = store.Create(request.Name.Trim(), request.Goal.Trim());
    return Results.Created($"/projects/{project.Id}", project);
})
.WithName("CreateProject");

app.MapGet("/projects/{projectId}", (string projectId, IProjectStore store) =>
{
    var project = store.Get(projectId);
    return project is null ? Results.NotFound(new ErrorResponse("project_not_found", "Project was not found.")) : Results.Ok(project);
})
.WithName("GetProject");

app.MapPost("/workflow/start", async (StartWorkflowRequest request, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.ProjectId) || string.IsNullOrWhiteSpace(request.Input))
    {
        return Results.BadRequest(new ErrorResponse("workflow_validation_failed", "Project id and input are required."));
    }

    if (store.Get(request.ProjectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    try
    {
        var response = await agentClient.StartWorkflowAsync(request, cancellationToken);
        return Results.Ok(response);
    }
    catch (AgentServiceException exc) when (exc.StatusCode == System.Net.HttpStatusCode.BadRequest)
    {
        return Results.BadRequest(new ErrorResponse("workflow_validation_failed", exc.Message));
    }
    catch (AgentServiceException exc)
    {
        return Results.Problem(exc.Message, statusCode: (int)exc.StatusCode);
    }
})
.WithName("StartWorkflow");

app.MapPost("/workflow/resume", async (ResumeWorkflowRequest request, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.ProjectId))
    {
        return Results.BadRequest(new ErrorResponse("workflow_validation_failed", "Project id is required."));
    }

    if (store.Get(request.ProjectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    try
    {
        var response = await agentClient.ResumeWorkflowAsync(request, cancellationToken);
        return Results.Ok(response);
    }
    catch (AgentServiceException exc) when (exc.StatusCode == System.Net.HttpStatusCode.NotFound)
    {
        return Results.NotFound(new ErrorResponse("workflow_not_found", exc.Message));
    }
    catch (AgentServiceException exc)
    {
        return Results.Problem(exc.Message, statusCode: (int)exc.StatusCode);
    }
})
.WithName("ResumeWorkflow");

app.MapGet("/workflow/{projectId}/status", async (string projectId, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetWorkflowStateAsync(projectId, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("workflow_not_found", "Workflow state was not found."))
        : Results.Ok(response);
})
.WithName("GetWorkflowStatus");

app.MapGet("/sections/{projectId}", async (string projectId, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetSectionsAsync(projectId, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("sections_not_found", "Sections were not found."))
        : Results.Ok(response);
})
.WithName("GetSections");

app.MapGet("/sections/{projectId}/{artifactType}/{sectionName}", async (string projectId, string artifactType, string sectionName, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(artifactType) || string.IsNullOrWhiteSpace(sectionName))
    {
        return Results.BadRequest(new ErrorResponse("section_validation_failed", "Artifact type and section name are required."));
    }

    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetSectionAsync(projectId, artifactType, sectionName, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("section_not_found", "Section was not found."))
        : Results.Ok(response);
})
.WithName("GetSection");

app.MapPut("/sections/{projectId}/{artifactType}/{sectionName}", async (string projectId, string artifactType, string sectionName, UpdateSectionRequest request, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(artifactType) || string.IsNullOrWhiteSpace(sectionName) || request.Content is null)
    {
        return Results.BadRequest(new ErrorResponse("section_validation_failed", "Artifact type, section name, and content are required."));
    }

    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.UpdateSectionAsync(projectId, artifactType, sectionName, request, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("section_not_found", "Section was not found."))
        : Results.Ok(response);
})
.WithName("UpdateSection");

app.MapGet("/sections/{projectId}/{artifactType}/{sectionName}/versions", async (string projectId, string artifactType, string sectionName, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(artifactType) || string.IsNullOrWhiteSpace(sectionName))
    {
        return Results.BadRequest(new ErrorResponse("section_validation_failed", "Artifact type and section name are required."));
    }

    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetSectionVersionsAsync(projectId, artifactType, sectionName, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("section_not_found", "Section was not found."))
        : Results.Ok(response);
})
.WithName("GetSectionVersions");

app.MapGet("/checkpoints/{projectId}", async (string projectId, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetCheckpointsAsync(projectId, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("checkpoints_not_found", "Checkpoints were not found."))
        : Results.Ok(response);
})
.WithName("GetCheckpoints");

app.MapGet("/logs/llm/{projectId}", async (string projectId, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetLlmLogsAsync(projectId, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("llm_logs_not_found", "LLM logs were not found."))
        : Results.Ok(response);
})
.WithName("GetLlmLogs");

app.MapGet("/metrics/workflow/{projectId}", async (string projectId, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetWorkflowMetricsAsync(projectId, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("workflow_metrics_not_found", "Workflow metrics were not found."))
        : Results.Ok(response);
})
.WithName("GetWorkflowMetrics");

app.MapGet("/llm/providers", async (IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    var response = await agentClient.GetLlmProvidersAsync(cancellationToken);
    return Results.Ok(response);
})
.WithName("GetLlmProviders");

app.MapGet("/projects/{projectId}/llm-settings", async (string projectId, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetProjectLlmSettingsAsync(projectId, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("llm_settings_not_found", "LLM settings were not found."))
        : Results.Ok(response);
})
.WithName("GetProjectLlmSettings");

app.MapPut("/projects/{projectId}/llm-settings", async (string projectId, ProjectLlmSettingsUpdateRequest request, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    if (request.Agents.Count == 0)
    {
        return Results.BadRequest(new ErrorResponse("llm_settings_validation_failed", "At least one agent setting is required."));
    }

    try
    {
        var response = await agentClient.UpdateProjectLlmSettingsAsync(projectId, request, cancellationToken);
        return Results.Ok(response);
    }
    catch (AgentServiceException exc) when (exc.StatusCode == System.Net.HttpStatusCode.BadRequest)
    {
        return Results.BadRequest(new ErrorResponse("llm_settings_validation_failed", exc.Message));
    }
    catch (AgentServiceException exc)
    {
        return Results.Problem(exc.Message, statusCode: (int)exc.StatusCode);
    }
})
.WithName("UpdateProjectLlmSettings");

app.MapPost("/rag/sources", async (RagSourceCreateRequest request, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.ProjectId) ||
        string.IsNullOrWhiteSpace(request.FileName) ||
        string.IsNullOrWhiteSpace(request.Content))
    {
        return Results.BadRequest(new ErrorResponse("rag_source_validation_failed", "Project id, file name, and content are required."));
    }

    var sourceType = (request.SourceType ?? "").Trim().ToLowerInvariant();
    var allowedSourceTypes = new[] { "txt", "pdf", "docx" };
    if (!allowedSourceTypes.Contains(sourceType))
    {
        return Results.BadRequest(new ErrorResponse("rag_source_type_invalid", "sourceType must be txt, pdf, or docx."));
    }

    if (store.Get(request.ProjectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    try
    {
        var response = await agentClient.CreateRagSourceAsync(request with { SourceType = sourceType }, cancellationToken);
        return Results.Created($"/rag/sources/{request.ProjectId}", response);
    }
    catch (AgentServiceException exc) when (exc.StatusCode == System.Net.HttpStatusCode.BadRequest)
    {
        return Results.BadRequest(new ErrorResponse("rag_source_validation_failed", exc.Message));
    }
})
.WithName("CreateRagSource");

app.MapGet("/rag/sources/{projectId}", async (string projectId, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    if (store.Get(projectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    var response = await agentClient.GetRagSourcesAsync(projectId, cancellationToken);
    return response is null
        ? Results.NotFound(new ErrorResponse("rag_sources_not_found", "RAG sources were not found."))
        : Results.Ok(response);
})
.WithName("GetRagSources");

app.MapPost("/hitl/action", async (HitlActionRequest request, IProjectStore store, IAgentServiceClient agentClient, CancellationToken cancellationToken) =>
{
    var allowedActions = new[] { "approve", "edit", "regenerate" };
    var allowedModes = new[] { "single", "cascade" };

    if (!allowedActions.Contains(request.Action, StringComparer.OrdinalIgnoreCase))
    {
        return Results.BadRequest(new ErrorResponse("hitl_action_invalid", "Action must be approve, edit, or regenerate."));
    }

    if (!string.IsNullOrWhiteSpace(request.Mode) && !allowedModes.Contains(request.Mode, StringComparer.OrdinalIgnoreCase))
    {
        return Results.BadRequest(new ErrorResponse("hitl_mode_invalid", "Mode must be single or cascade."));
    }

    if (request.Action.Equals("edit", StringComparison.OrdinalIgnoreCase))
    {
        if (string.IsNullOrWhiteSpace(request.Section) || request.Content is null)
        {
            return Results.BadRequest(new ErrorResponse("hitl_edit_invalid", "Section and content are required for edit actions."));
        }
    }

    if (request.Action.Equals("regenerate", StringComparison.OrdinalIgnoreCase) && string.IsNullOrWhiteSpace(request.Section))
    {
        return Results.BadRequest(new ErrorResponse("hitl_regenerate_invalid", "Section is required for regenerate actions."));
    }

    if (store.Get(request.ProjectId) is null)
    {
        return Results.NotFound(new ErrorResponse("project_not_found", "Project was not found."));
    }

    try
    {
        var response = await agentClient.SendHitlActionAsync(request, cancellationToken);
        return Results.Ok(response);
    }
    catch (AgentServiceException exc) when (exc.StatusCode == System.Net.HttpStatusCode.BadRequest)
    {
        return Results.BadRequest(new ErrorResponse("hitl_validation_failed", exc.Message));
    }
    catch (AgentServiceException exc) when (exc.StatusCode == System.Net.HttpStatusCode.NotFound)
    {
        return Results.NotFound(new ErrorResponse("workflow_not_found", exc.Message));
    }
})
.WithName("HitlAction");

app.Run();
