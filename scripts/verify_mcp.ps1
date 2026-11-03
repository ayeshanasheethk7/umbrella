$filePath = "C:\Users\DELL\.gemini\config\mcp_config.json"
if (-not (Test-Path $filePath)) {
    Write-Error "File not found: $filePath"
    exit 1
}

$content = Get-Content -Path $filePath -Raw
try {
    $json = ConvertFrom-Json -InputObject $content -ErrorAction Stop
    Write-Output "JSON SYNTAX: VALID"
} catch {
    Write-Error "JSON SYNTAX: INVALID - $_"
    exit 1
}

$servers = $json.mcpServers.PSObject.Properties
Write-Output "Configured Servers count: $($servers.Count)"

foreach ($server in $servers) {
    Write-Output "=== Server: $($server.Name) ==="
    Write-Output "Command: $($server.Value.command)"
    Write-Output "Args: $($server.Value.args -join ' ')"
    Write-Output "Description: $($server.Value.description)"
    if ($server.Value.env) {
        Write-Output "Environment Variables:"
        foreach ($envProp in $server.Value.env.PSObject.Properties) {
            Write-Output "  $($envProp.Name) = $($envProp.Value)"
        }
    } else {
        Write-Output "Environment Variables: None"
    }
}
