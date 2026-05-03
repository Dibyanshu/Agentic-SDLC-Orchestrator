using System.Text.Json;
using AgenticSdlc.Api.Contracts;

namespace AgenticSdlc.Api.Tests;

public sealed class ContractTests
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    [Fact]
    public void RagSourceCreateRequest_DeserializesCamelCasePayload()
    {
        const string payload = """
        {
          "projectId": "project-1",
          "fileName": "context.txt",
          "content": "Project context",
          "sourceType": "txt"
        }
        """;

        var request = JsonSerializer.Deserialize<RagSourceCreateRequest>(payload, JsonOptions);

        Assert.NotNull(request);
        Assert.Equal("project-1", request.ProjectId);
        Assert.Equal("context.txt", request.FileName);
        Assert.Equal("Project context", request.Content);
        Assert.Equal("txt", request.SourceType);
    }

    [Theory]
    [InlineData("approve", null, null, null)]
    [InlineData("edit", "PRD.Features", "Updated features", null)]
    [InlineData("regenerate", "BA.UserStories", null, "cascade")]
    public void HitlActionRequest_SupportsExpectedActions(
        string action,
        string? section,
        string? content,
        string? mode)
    {
        var request = new HitlActionRequest(
            ProjectId: "project-1",
            Action: action,
            Section: section,
            Content: content,
            Mode: mode);

        Assert.Equal("project-1", request.ProjectId);
        Assert.Equal(action, request.Action);
        Assert.Equal(section, request.Section);
        Assert.Equal(content, request.Content);
        Assert.Equal(mode, request.Mode);
    }

    [Fact]
    public void WorkflowMetricsResponse_PreservesLatencyByNode()
    {
        var metrics = new WorkflowMetricsResponse(
            ProjectId: "project-1",
            TotalInputTokens: 10,
            TotalOutputTokens: 15,
            TotalTokens: 25,
            EstimatedCost: "0.000100",
            CacheHitCount: 1,
            LlmCallCount: 2,
            RefinementCount: 3,
            LatencyByNode:
            [
                new NodeLatencyMetric("pm_node", 1, 120, 120.0),
            ]);

        Assert.Equal(25, metrics.TotalTokens);
        Assert.Single(metrics.LatencyByNode);
        Assert.Equal("pm_node", metrics.LatencyByNode[0].NodeName);
    }

    [Fact]
    public void LlmSettingsUpdateRequest_DeserializesAgentMap()
    {
        const string payload = """
        {
          "agents": {
            "pm": { "provider": "stub", "model": "stub", "tokenBudget": 3000 },
            "ba": { "provider": "gemini", "model": "gemini-2.5-flash", "tokenBudget": 3000 },
            "architect": { "provider": "claude", "model": "claude-3-5-sonnet-20241022", "tokenBudget": 4000 }
          }
        }
        """;

        var request = JsonSerializer.Deserialize<ProjectLlmSettingsUpdateRequest>(payload, JsonOptions);

        Assert.NotNull(request);
        Assert.Equal("stub", request.Agents["pm"].Provider);
        Assert.Equal("gemini-2.5-flash", request.Agents["ba"].Model);
        Assert.Equal(4000, request.Agents["architect"].TokenBudget);
    }

    [Fact]
    public void LlmProvidersResponse_SerializesKeyStatus()
    {
        var response = new LlmProvidersResponse(
        [
            new LlmProviderResponse("stub", "stub", true),
            new LlmProviderResponse("gemini", "gemini-2.5-flash", false),
        ]);

        var json = JsonSerializer.Serialize(response, JsonOptions);

        Assert.Contains("apiKeyConfigured", json);
        Assert.Contains("defaultModel", json);
    }
}
