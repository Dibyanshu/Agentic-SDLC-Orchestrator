using System.Net.Http.Json;
using AgenticSdlc.Api.Contracts;

namespace AgenticSdlc.Api.Services;

public interface IAgentServiceClient
{
    Task<WorkflowResponse> StartWorkflowAsync(StartWorkflowRequest request, CancellationToken cancellationToken);
    Task<WorkflowResponse> ResumeWorkflowAsync(ResumeWorkflowRequest request, CancellationToken cancellationToken);
    Task<WorkflowResponse> SendHitlActionAsync(HitlActionRequest request, CancellationToken cancellationToken);
    Task<WorkflowResponse?> GetWorkflowStateAsync(string projectId, CancellationToken cancellationToken);
    Task<SectionsResponse?> GetSectionsAsync(string projectId, CancellationToken cancellationToken);
    Task<SectionResponse?> GetSectionAsync(string projectId, string artifactType, string sectionName, CancellationToken cancellationToken);
    Task<SectionResponse?> UpdateSectionAsync(string projectId, string artifactType, string sectionName, UpdateSectionRequest request, CancellationToken cancellationToken);
    Task<SectionVersionsResponse?> GetSectionVersionsAsync(string projectId, string artifactType, string sectionName, CancellationToken cancellationToken);
    Task<CheckpointsResponse?> GetCheckpointsAsync(string projectId, CancellationToken cancellationToken);
    Task<LlmLogsResponse?> GetLlmLogsAsync(string projectId, CancellationToken cancellationToken);
}

public sealed class AgentServiceClient(HttpClient httpClient) : IAgentServiceClient
{
    public async Task<WorkflowResponse> StartWorkflowAsync(StartWorkflowRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/workflow/start", request, cancellationToken);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<WorkflowResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty workflow response.");
    }

    public async Task<WorkflowResponse> ResumeWorkflowAsync(ResumeWorkflowRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/workflow/resume", request, cancellationToken);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<WorkflowResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty workflow response.");
    }

    public async Task<WorkflowResponse> SendHitlActionAsync(HitlActionRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/workflow/hitl", request, cancellationToken);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<WorkflowResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty workflow response.");
    }

    public async Task<WorkflowResponse?> GetWorkflowStateAsync(string projectId, CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync($"/workflow/{projectId}/state", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<WorkflowResponse>(cancellationToken: cancellationToken);
    }

    public async Task<SectionsResponse?> GetSectionsAsync(string projectId, CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync($"/sections/{projectId}", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<SectionsResponse>(cancellationToken: cancellationToken);
    }

    public async Task<SectionResponse?> GetSectionAsync(
        string projectId,
        string artifactType,
        string sectionName,
        CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync(
            $"/sections/{Escape(projectId)}/{Escape(artifactType)}/{Escape(sectionName)}",
            cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<SectionResponse>(cancellationToken: cancellationToken);
    }

    public async Task<SectionResponse?> UpdateSectionAsync(
        string projectId,
        string artifactType,
        string sectionName,
        UpdateSectionRequest request,
        CancellationToken cancellationToken)
    {
        var response = await httpClient.PutAsJsonAsync(
            $"/sections/{Escape(projectId)}/{Escape(artifactType)}/{Escape(sectionName)}",
            request,
            cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<SectionResponse>(cancellationToken: cancellationToken);
    }

    public async Task<SectionVersionsResponse?> GetSectionVersionsAsync(
        string projectId,
        string artifactType,
        string sectionName,
        CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync(
            $"/sections/{Escape(projectId)}/{Escape(artifactType)}/{Escape(sectionName)}/versions",
            cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<SectionVersionsResponse>(cancellationToken: cancellationToken);
    }

    public async Task<CheckpointsResponse?> GetCheckpointsAsync(string projectId, CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync($"/checkpoints/{projectId}", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<CheckpointsResponse>(cancellationToken: cancellationToken);
    }

    public async Task<LlmLogsResponse?> GetLlmLogsAsync(string projectId, CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync($"/logs/llm/{Escape(projectId)}", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<LlmLogsResponse>(cancellationToken: cancellationToken);
    }

    private static string Escape(string value) => Uri.EscapeDataString(value);
}
