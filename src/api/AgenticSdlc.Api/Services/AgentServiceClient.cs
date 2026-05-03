using System.Net.Http.Json;
using System.Text.Json;
using AgenticSdlc.Api.Contracts;

namespace AgenticSdlc.Api.Services;

public sealed class AgentServiceException(System.Net.HttpStatusCode statusCode, string message) : Exception(message)
{
    public System.Net.HttpStatusCode StatusCode { get; } = statusCode;
}

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
    Task<WorkflowMetricsResponse?> GetWorkflowMetricsAsync(string projectId, CancellationToken cancellationToken);
    Task<RagSourceResponse> CreateRagSourceAsync(RagSourceCreateRequest request, CancellationToken cancellationToken);
    Task<RagSourcesResponse?> GetRagSourcesAsync(string projectId, CancellationToken cancellationToken);
    Task<bool> DeleteRagSourceAsync(string sourceId, CancellationToken cancellationToken);
    Task<LlmProvidersResponse> GetLlmProvidersAsync(CancellationToken cancellationToken);
    Task<ProjectLlmSettingsResponse?> GetProjectLlmSettingsAsync(string projectId, CancellationToken cancellationToken);
    Task<ProjectLlmSettingsResponse> UpdateProjectLlmSettingsAsync(string projectId, ProjectLlmSettingsUpdateRequest request, CancellationToken cancellationToken);
}

public sealed class AgentServiceClient(HttpClient httpClient) : IAgentServiceClient
{
    public async Task<WorkflowResponse> StartWorkflowAsync(StartWorkflowRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/workflow/start", request, cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            var message = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new AgentServiceException(response.StatusCode, ExtractErrorMessage(message));
        }

        return await response.Content.ReadFromJsonAsync<WorkflowResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty workflow response.");
    }

    public async Task<WorkflowResponse> ResumeWorkflowAsync(ResumeWorkflowRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/workflow/resume", request, cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            var message = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new AgentServiceException(response.StatusCode, ExtractErrorMessage(message));
        }

        return await response.Content.ReadFromJsonAsync<WorkflowResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty workflow response.");
    }

    public async Task<WorkflowResponse> SendHitlActionAsync(HitlActionRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/workflow/hitl", request, cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            var message = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new AgentServiceException(response.StatusCode, ExtractErrorMessage(message));
        }

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

    public async Task<WorkflowMetricsResponse?> GetWorkflowMetricsAsync(string projectId, CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync($"/metrics/workflow/{Escape(projectId)}", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<WorkflowMetricsResponse>(cancellationToken: cancellationToken);
    }

    public async Task<RagSourceResponse> CreateRagSourceAsync(RagSourceCreateRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/rag/sources", request, cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            var message = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new AgentServiceException(response.StatusCode, ExtractErrorMessage(message));
        }

        return await response.Content.ReadFromJsonAsync<RagSourceResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty RAG source response.");
    }

    public async Task<RagSourcesResponse?> GetRagSourcesAsync(string projectId, CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync($"/rag/sources/{Escape(projectId)}", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<RagSourcesResponse>(cancellationToken: cancellationToken);
    }

    public async Task<bool> DeleteRagSourceAsync(string sourceId, CancellationToken cancellationToken)
    {
        var response = await httpClient.DeleteAsync($"/rag/sources/{Escape(sourceId)}", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return false;
        }

        if (!response.IsSuccessStatusCode)
        {
            var message = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new AgentServiceException(response.StatusCode, ExtractErrorMessage(message));
        }

        return true;
    }

    public async Task<LlmProvidersResponse> GetLlmProvidersAsync(CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync("/llm/providers", cancellationToken);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<LlmProvidersResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty LLM providers response.");
    }

    public async Task<ProjectLlmSettingsResponse?> GetProjectLlmSettingsAsync(string projectId, CancellationToken cancellationToken)
    {
        var response = await httpClient.GetAsync($"/projects/{Escape(projectId)}/llm-settings", cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<ProjectLlmSettingsResponse>(cancellationToken: cancellationToken);
    }

    public async Task<ProjectLlmSettingsResponse> UpdateProjectLlmSettingsAsync(
        string projectId,
        ProjectLlmSettingsUpdateRequest request,
        CancellationToken cancellationToken)
    {
        var response = await httpClient.PutAsJsonAsync($"/projects/{Escape(projectId)}/llm-settings", request, cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            var message = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new AgentServiceException(response.StatusCode, ExtractErrorMessage(message));
        }

        return await response.Content.ReadFromJsonAsync<ProjectLlmSettingsResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty LLM settings response.");
    }

    private static string Escape(string value) => Uri.EscapeDataString(value);

    private static string ExtractErrorMessage(string content)
    {
        if (string.IsNullOrWhiteSpace(content))
        {
            return "Agent service request failed.";
        }

        try
        {
            using var document = JsonDocument.Parse(content);
            if (document.RootElement.TryGetProperty("detail", out var detail))
            {
                return detail.GetString() ?? content;
            }
        }
        catch (JsonException)
        {
            return content;
        }

        return content;
    }
}
