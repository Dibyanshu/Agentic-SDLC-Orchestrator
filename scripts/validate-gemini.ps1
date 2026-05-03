param(
    [string]$ApiBaseUrl = "http://localhost:8080",
    [string]$GeminiModel = ""
)

$ErrorActionPreference = "Stop"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw "Gemini validation failed: $Message"
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

Write-Host "Checking API and Gemini provider configuration..."
Wait-HttpOk -Uri "$ApiBaseUrl/health"

$providers = Invoke-Json -Method Get -Uri "$ApiBaseUrl/llm/providers"
$geminiProvider = $providers.providers | Where-Object { $_.provider -eq "gemini" } | Select-Object -First 1
Assert-True ($null -ne $geminiProvider) "Gemini provider was not returned by /llm/providers."
Assert-True ($geminiProvider.apiKeyConfigured -eq $true) "GEMINI_API_KEY is not configured for the running agent-service container."

if ([string]::IsNullOrWhiteSpace($GeminiModel)) {
    $GeminiModel = "gemini-2.5-flash"
}

Write-Host "Creating Gemini validation project..."
$suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$project = Invoke-Json -Method Post -Uri "$ApiBaseUrl/projects" -Body @{
    name = "Gemini Validate $suffix"
    goal = "Validate Gemini PM generation only"
}

Write-Host "Uploading small TXT RAG context..."
$null = Invoke-Json -Method Post -Uri "$ApiBaseUrl/rag/sources" -Body @{
    projectId = $project.id
    fileName = "gemini-context.txt"
    content = "Validate that Gemini can generate concise PRD JSON using uploaded TXT RAG context, logs, token usage, latency, and cache key traceability."
    sourceType = "txt"
}

Write-Host "Saving PM=Gemini, BA/Architect=stub settings..."
$settings = @{
    agents = @{
        pm = @{ provider = "gemini"; model = $GeminiModel; tokenBudget = 3000 }
        ba = @{ provider = "stub"; model = "stub"; tokenBudget = 3000 }
        architect = @{ provider = "stub"; model = "stub"; tokenBudget = 4000 }
    }
}
$null = Invoke-Json -Method Put -Uri "$ApiBaseUrl/projects/$($project.id)/llm-settings" -Body $settings

$inputText = "Build a minimal controlled RAG validation feature for Gemini smoke test $suffix."

Write-Host "Starting workflow once; this should make one Gemini PM call..."
$workflow = Invoke-Json -Method Post -Uri "$ApiBaseUrl/workflow/start" -Body @{
    projectId = $project.id
    input = $inputText
}
Assert-True ($workflow.status -eq "paused_for_hitl") "Workflow did not pause after PRD generation."

$sections = Invoke-Json -Method Get -Uri "$ApiBaseUrl/sections/$($project.id)"
Assert-True (($sections.sections | Where-Object { $_.artifactType -eq "PRD" }).Count -ge 3) "PRD sections were not generated."

$logs = Invoke-Json -Method Get -Uri "$ApiBaseUrl/logs/llm/$($project.id)"
$firstLog = $logs.logs[0]
Assert-True ($firstLog.status -eq "success") "Gemini LLM log status was not success."
Assert-True ($firstLog.modelName -like "gemini:*") "LLM log modelName was not a Gemini model."
Assert-True ($firstLog.inputTokens -gt 0) "Gemini log did not include input token usage."
Assert-True ($firstLog.outputTokens -gt 0) "Gemini log did not include output token usage."
Assert-True ($firstLog.latencyMs -ge 0) "Gemini log did not include latency."
Assert-True (-not [string]::IsNullOrWhiteSpace($firstLog.cacheKey)) "Gemini log did not include cache key."
Assert-True ($firstLog.contextPayload.rag_chunks.Count -ge 1) "Gemini log did not include RAG chunks."
Assert-True ($firstLog.cacheHit -eq $false) "First Gemini validation call unexpectedly came from cache."

$parsedResponse = $firstLog.responseText | ConvertFrom-Json
Assert-True (-not [string]::IsNullOrWhiteSpace($parsedResponse.Overview)) "Gemini response JSON did not include Overview."
Assert-True (-not [string]::IsNullOrWhiteSpace($parsedResponse.Features)) "Gemini response JSON did not include Features."
Assert-True (-not [string]::IsNullOrWhiteSpace($parsedResponse.UserFlow)) "Gemini response JSON did not include UserFlow."

Write-Host "Starting workflow again with identical input/settings; this should be cache-only..."
$null = Invoke-Json -Method Post -Uri "$ApiBaseUrl/workflow/start" -Body @{
    projectId = $project.id
    input = $inputText
}

$cacheLogs = Invoke-Json -Method Get -Uri "$ApiBaseUrl/logs/llm/$($project.id)"
$cacheLog = $cacheLogs.logs[0]
Assert-True ($cacheLog.cacheHit -eq $true) "Second identical Gemini validation request did not use cache."
Assert-True ($cacheLog.modelName -like "gemini:*") "Cached Gemini log did not preserve model name."

Write-Host "Gemini validation passed for project $($project.id) using model $GeminiModel."
