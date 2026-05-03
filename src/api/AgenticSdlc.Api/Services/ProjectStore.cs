using AgenticSdlc.Api.Contracts;
using MySqlConnector;

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

public sealed class MySqlProjectStore(IConfiguration configuration) : IProjectStore
{
    private readonly string _connectionString = configuration.GetConnectionString("Default")
        ?? Environment.GetEnvironmentVariable("DB_CONNECTION")
        ?? throw new InvalidOperationException("ConnectionStrings:Default or DB_CONNECTION must be configured.");

    public ProjectResponse Create(string name, string goal)
    {
        var project = new ProjectResponse(
            Guid.NewGuid().ToString("n"),
            name,
            goal,
            DateTimeOffset.UtcNow);

        using var connection = new MySqlConnection(_connectionString);
        connection.Open();

        using var command = connection.CreateCommand();
        command.CommandText = """
            INSERT INTO projects (id, name, goal, created_at, updated_at)
            VALUES (@id, @name, @goal, @createdAt, @createdAt);
            """;
        command.Parameters.AddWithValue("@id", project.Id);
        command.Parameters.AddWithValue("@name", project.Name);
        command.Parameters.AddWithValue("@goal", project.Goal);
        command.Parameters.AddWithValue("@createdAt", project.CreatedAt.UtcDateTime);
        command.ExecuteNonQuery();

        return project;
    }

    public ProjectResponse? Get(string id)
    {
        using var connection = new MySqlConnection(_connectionString);
        connection.Open();

        using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT id, name, goal, created_at
            FROM projects
            WHERE id = @id
            LIMIT 1;
            """;
        command.Parameters.AddWithValue("@id", id);

        using var reader = command.ExecuteReader();
        if (!reader.Read())
        {
            return null;
        }

        return new ProjectResponse(
            reader.GetString("id"),
            reader.GetString("name"),
            reader.GetString("goal"),
            new DateTimeOffset(DateTime.SpecifyKind(reader.GetDateTime("created_at"), DateTimeKind.Utc)));
    }
}
