param(
    [string]$ApiBaseUrl = "http://localhost:8080",
    [string]$UiBaseUrl = "http://localhost:5173"
)

$ErrorActionPreference = "Stop"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw "Smoke test failed: $Message"
    }
}

function Invoke-Json {
    param(
        [string]$Method,
        [string]$Uri,
        [object]$Body = $null
    )

    $parameters = @{
        Method = $Method
        Uri = $Uri
    }

    if ($null -ne $Body) {
        $parameters.ContentType = "application/json"
        $parameters.Body = ($Body | ConvertTo-Json -Depth 20)
    }

    Invoke-RestMethod @parameters
}

function Wait-HttpOk {
    param(
        [string]$Uri,
        [int]$Attempts = 30
    )

    for ($index = 1; $index -le $Attempts; $index++) {
        try {
            $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                return $response
            }
        }
        catch {
            if ($index -eq $Attempts) {
                throw
            }
        }

        Start-Sleep -Seconds 1
    }

    throw "Smoke test failed: $Uri did not return HTTP 200."
}

Write-Host "Checking UI and API health..."
$uiStatus = Wait-HttpOk -Uri $UiBaseUrl
Assert-True ($uiStatus.StatusCode -eq 200) "UI did not return HTTP 200."

$null = Wait-HttpOk -Uri "$ApiBaseUrl/health"
$health = Invoke-Json -Method Get -Uri "$ApiBaseUrl/health"
Assert-True ($health.status -eq "ok") "API health check did not return ok."

Write-Host "Creating project..."
$suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$project = Invoke-Json -Method Post -Uri "$ApiBaseUrl/projects" -Body @{
    name = "Smoke $suffix"
    goal = "Validate full Agentic SDLC happy path"
}
Assert-True (-not [string]::IsNullOrWhiteSpace($project.id)) "Project id was empty."

Write-Host "Uploading TXT RAG source..."
$source = Invoke-Json -Method Post -Uri "$ApiBaseUrl/rag/sources" -Body @{
    projectId = $project.id
    fileName = "smoke-context.txt"
    content = "Critical context: generate PRD, BA, and architecture for controlled TXT RAG ingestion, Chroma retrieval, HITL approvals, LLM logs, and metrics."
    sourceType = "txt"
}
Assert-True ($source.chunkCount -gt 0) "RAG source had no chunks."

$sources = Invoke-Json -Method Get -Uri "$ApiBaseUrl/rag/sources/$($project.id)"
Assert-True ($sources.sources.Count -ge 1) "RAG source was not listed."

Write-Host "Saving per-agent LLM settings..."
$settings = Invoke-Json -Method Put -Uri "$ApiBaseUrl/projects/$($project.id)/llm-settings" -Body @{
    agents = @{
        pm = @{ provider = "stub"; model = "stub"; tokenBudget = 3100 }
        ba = @{ provider = "stub"; model = "stub"; tokenBudget = 3200 }
        architect = @{ provider = "stub"; model = "stub"; tokenBudget = 4300 }
    }
}
Assert-True ($settings.agents.pm.tokenBudget -eq 3100) "PM LLM settings were not saved."

Write-Host "Starting workflow..."
$workflow = Invoke-Json -Method Post -Uri "$ApiBaseUrl/workflow/start" -Body @{
    projectId = $project.id
    input = "Build the controlled RAG ingestion feature with HITL traceability."
}
Assert-True ($workflow.status -eq "paused_for_hitl") "Workflow did not pause for PRD HITL."

$sections = Invoke-Json -Method Get -Uri "$ApiBaseUrl/sections/$($project.id)"
Assert-True (($sections.sections | Where-Object { $_.artifactType -eq "PRD" }).Count -ge 3) "PRD sections were not generated."

$logs = Invoke-Json -Method Get -Uri "$ApiBaseUrl/logs/llm/$($project.id)"
Assert-True ($logs.logs.Count -ge 1) "No LLM logs were recorded."
Assert-True ($logs.logs[0].contextPayload.rag_chunks.Count -ge 1) "LLM log did not include RAG chunks."
Assert-True ($logs.logs[0].contextPayload.llm_settings.provider -eq "stub") "LLM log did not include selected provider."
Assert-True ($logs.logs[0].contextPayload.llm_settings.token_budget -eq 3100) "LLM log did not include selected token budget."

Write-Host "Approving PRD, BA, and Architecture..."
$workflow = Invoke-Json -Method Post -Uri "$ApiBaseUrl/hitl/action" -Body @{
    projectId = $project.id
    action = "approve"
}
Assert-True ($workflow.status -eq "paused_for_hitl") "Workflow did not pause after BA generation."

$workflow = Invoke-Json -Method Post -Uri "$ApiBaseUrl/hitl/action" -Body @{
    projectId = $project.id
    action = "approve"
}
Assert-True ($workflow.status -eq "paused_for_hitl") "Workflow did not pause after Architecture generation."

$workflow = Invoke-Json -Method Post -Uri "$ApiBaseUrl/hitl/action" -Body @{
    projectId = $project.id
    action = "approve"
}
Assert-True ($workflow.status -eq "completed") "Workflow did not complete after final approval."

$metrics = Invoke-Json -Method Get -Uri "$ApiBaseUrl/metrics/workflow/$($project.id)"
Assert-True ($metrics.llmCallCount -ge 3) "Metrics did not include expected LLM calls."

$checkpoints = Invoke-Json -Method Get -Uri "$ApiBaseUrl/checkpoints/$($project.id)"
Assert-True ($checkpoints.checkpoints.Count -ge 3) "Expected checkpoints were not found."

Write-Host "Checking response cache..."
$cacheInput = "Build a cached workflow request for deterministic PM output."
$cacheProjectA = Invoke-Json -Method Post -Uri "$ApiBaseUrl/projects" -Body @{
    name = "Cache A $suffix"
    goal = "Validate response cache"
}
$cacheProjectB = Invoke-Json -Method Post -Uri "$ApiBaseUrl/projects" -Body @{
    name = "Cache B $suffix"
    goal = "Validate response cache"
}

$cacheSettings = @{
    agents = @{
        pm = @{ provider = "stub"; model = "stub"; tokenBudget = 3000 }
        ba = @{ provider = "stub"; model = "stub"; tokenBudget = 3000 }
        architect = @{ provider = "stub"; model = "stub"; tokenBudget = 4000 }
    }
}
$null = Invoke-Json -Method Put -Uri "$ApiBaseUrl/projects/$($cacheProjectA.id)/llm-settings" -Body $cacheSettings
$null = Invoke-Json -Method Put -Uri "$ApiBaseUrl/projects/$($cacheProjectB.id)/llm-settings" -Body $cacheSettings

$null = Invoke-Json -Method Post -Uri "$ApiBaseUrl/workflow/start" -Body @{
    projectId = $cacheProjectA.id
    input = $cacheInput
}
$null = Invoke-Json -Method Post -Uri "$ApiBaseUrl/workflow/start" -Body @{
    projectId = $cacheProjectB.id
    input = $cacheInput
}

$cacheLogs = Invoke-Json -Method Get -Uri "$ApiBaseUrl/logs/llm/$($cacheProjectB.id)"
Assert-True ($cacheLogs.logs[0].cacheHit -eq $true) "Repeated prompt/context did not use the response cache."

$cacheMetrics = Invoke-Json -Method Get -Uri "$ApiBaseUrl/metrics/workflow/$($cacheProjectB.id)"
Assert-True ($cacheMetrics.cacheHitCount -ge 1) "Metrics did not include the cache hit."

Write-Host "Smoke test passed for project $($project.id)."
