param(
    [string]$ApiBaseUrl = "http://localhost:8080",
    [string]$OpenAiModel = ""
)

$ErrorActionPreference = "Stop"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw "OpenAI validation failed: $Message"
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
                return
            }
        }
        catch {
            if ($index -eq $Attempts) {
                throw
            }
        }

        Start-Sleep -Seconds 1
    }
}

Write-Host "Checking API and OpenAI provider configuration..."
Wait-HttpOk -Uri "$ApiBaseUrl/health"

$providers = Invoke-Json -Method Get -Uri "$ApiBaseUrl/llm/providers"
$openaiProvider = $providers.providers | Where-Object { $_.provider -eq "openai" } | Select-Object -First 1
Assert-True ($null -ne $openaiProvider) "OpenAI provider was not returned by /llm/providers."
Assert-True ($openaiProvider.apiKeyConfigured -eq $true) "OPENAI_API_KEY is not configured for the running agent-service container."

if ([string]::IsNullOrWhiteSpace($OpenAiModel)) {
    $OpenAiModel = $openaiProvider.defaultModel
}

Write-Host "Creating OpenAI validation project..."
$suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$project = Invoke-Json -Method Post -Uri "$ApiBaseUrl/projects" -Body @{
    name = "OpenAI Validate $suffix"
    goal = "Validate OpenAI PM generation only"
}

Write-Host "Uploading small TXT RAG context..."
$null = Invoke-Json -Method Post -Uri "$ApiBaseUrl/rag/sources" -Body @{
    projectId = $project.id
    fileName = "openai-context.txt"
    content = "Validate that OpenAI can generate concise PRD JSON using uploaded TXT RAG context, logs, token usage, latency, and cache key traceability."
    sourceType = "txt"
}

Write-Host "Saving PM=OpenAI, BA/Architect=stub settings..."
$settings = @{
    agents = @{
        pm = @{ provider = "openai"; model = $OpenAiModel; tokenBudget = 3000 }
        ba = @{ provider = "stub"; model = "stub"; tokenBudget = 3000 }
        architect = @{ provider = "stub"; model = "stub"; tokenBudget = 4000 }
    }
}
$null = Invoke-Json -Method Put -Uri "$ApiBaseUrl/projects/$($project.id)/llm-settings" -Body $settings

$inputText = "Build a minimal controlled RAG validation feature for OpenAI smoke test $suffix."

Write-Host "Starting workflow once; this should make one OpenAI PM call..."
$workflow = Invoke-Json -Method Post -Uri "$ApiBaseUrl/workflow/start" -Body @{
    projectId = $project.id
    input = $inputText
}
Assert-True ($workflow.status -eq "paused_for_hitl") "Workflow did not pause after PRD generation."

$sections = Invoke-Json -Method Get -Uri "$ApiBaseUrl/sections/$($project.id)"
Assert-True (($sections.sections | Where-Object { $_.artifactType -eq "PRD" }).Count -ge 3) "PRD sections were not generated."

$logs = Invoke-Json -Method Get -Uri "$ApiBaseUrl/logs/llm/$($project.id)"
$firstLog = $logs.logs[0]
Assert-True ($firstLog.status -eq "success") "OpenAI LLM log status was not success."
Assert-True ($firstLog.modelName -like "openai:*") "LLM log modelName was not an OpenAI model."
Assert-True ($firstLog.inputTokens -gt 0) "OpenAI log did not include input token usage."
Assert-True ($firstLog.outputTokens -gt 0) "OpenAI log did not include output token usage."
Assert-True ($firstLog.latencyMs -ge 0) "OpenAI log did not include latency."
Assert-True (-not [string]::IsNullOrWhiteSpace($firstLog.cacheKey)) "OpenAI log did not include cache key."
Assert-True ($firstLog.contextPayload.rag_chunks.Count -ge 1) "OpenAI log did not include RAG chunks."
Assert-True ($firstLog.cacheHit -eq $false) "First OpenAI validation call unexpectedly came from cache."

$parsedResponse = $firstLog.responseText | ConvertFrom-Json
Assert-True (-not [string]::IsNullOrWhiteSpace($parsedResponse.Overview)) "OpenAI response JSON did not include Overview."
Assert-True (-not [string]::IsNullOrWhiteSpace($parsedResponse.Features)) "OpenAI response JSON did not include Features."
Assert-True (-not [string]::IsNullOrWhiteSpace($parsedResponse.UserFlow)) "OpenAI response JSON did not include UserFlow."

Write-Host "Starting workflow again with identical input/settings; this should be cache-only..."
$null = Invoke-Json -Method Post -Uri "$ApiBaseUrl/workflow/start" -Body @{
    projectId = $project.id
    input = $inputText
}

$cacheLogs = Invoke-Json -Method Get -Uri "$ApiBaseUrl/logs/llm/$($project.id)"
$cacheLog = $cacheLogs.logs[0]
Assert-True ($cacheLog.cacheHit -eq $true) "Second identical OpenAI validation request did not use cache."
Assert-True ($cacheLog.modelName -like "openai:*") "Cached OpenAI log did not preserve model name."

Write-Host "OpenAI validation passed for project $($project.id) using model $OpenAiModel."
