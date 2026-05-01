using System.Net.Http.Json;
using AgenticSdlc.Api.Contracts;

namespace AgenticSdlc.Api.Services;

public interface IAgentServiceClient
{
    Task<WorkflowResponse> StartWorkflowAsync(StartWorkflowRequest request, CancellationToken cancellationToken);
    Task<WorkflowResponse> SendHitlActionAsync(HitlActionRequest request, CancellationToken cancellationToken);
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

    public async Task<WorkflowResponse> SendHitlActionAsync(HitlActionRequest request, CancellationToken cancellationToken)
    {
        var response = await httpClient.PostAsJsonAsync("/workflow/hitl", request, cancellationToken);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<WorkflowResponse>(cancellationToken: cancellationToken)
            ?? throw new InvalidOperationException("Agent service returned an empty workflow response.");
    }
}

