using AgenticSdlc.Api.Contracts;

namespace AgenticSdlc.Api.Services;

public interface IProjectStore
{
    ProjectResponse Create(string name, string goal);
    ProjectResponse? Get(string id);
}

public sealed class InMemoryProjectStore : IProjectStore
{
    private readonly Dictionary<string, ProjectResponse> _projects = new(StringComparer.OrdinalIgnoreCase);
    private readonly object _gate = new();

    public ProjectResponse Create(string name, string goal)
    {
        var project = new ProjectResponse(
            Guid.NewGuid().ToString("n"),
            name,
            goal,
            DateTimeOffset.UtcNow);

        lock (_gate)
        {
            _projects[project.Id] = project;
        }

        return project;
    }

    public ProjectResponse? Get(string id)
    {
        lock (_gate)
        {
            return _projects.GetValueOrDefault(id);
        }
    }
}

