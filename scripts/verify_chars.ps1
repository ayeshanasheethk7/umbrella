$targets = @(
  "AGENTS.md",
  "GEMINI.md",
  ".agents\rules\01-design-system.md",
  ".agents\rules\02-security-privacy.md",
  ".agents\rules\03-typescript-nextjs.md",
  ".agents\rules\04-supabase-sql.md",
  "docs\SPEC.md",
  "docs\DECISIONS.md",
  "docs\PROGRESS.md",
  "docs\DB-RUNBOOK.md",
  "docs\DEPLOY.md",
  "docs\SWARM_COORDINATION.md",
  ".agents\skills\graphify\SKILL.md",
  ".agents\skills\subagent-handling\SKILL.md",
  "PROJECT.md"
)

$base = "c:\Users\DELL\ayesha_pro\medi_qr"
Write-Output "=== AUDIT: CHARACTER COUNT VERIFICATION (< 12,000 chars) ==="
foreach ($t in $targets) {
  $full = Join-Path $base $t
  if (Test-Path $full) {
    $content = Get-Content -Path $full -Raw
    $len = $content.Length
    $status = if ($len -lt 12000) { "PASS" } else { "FAIL (>12k)" }
    Write-Output ("{0,-42} : {1,6} chars : {2}" -f $t, $len, $status)
  } else {
    Write-Output ("{0,-42} : MISSING" -f $t)
  }
}

Write-Output "`n=== AUDIT: MCP CONFIGURATION SYNTAX ==="
$mcpFile = "C:\Users\DELL\.gemini\config\mcp_config.json"
if (Test-Path $mcpFile) {
  try {
    $raw = Get-Content -Path $mcpFile -Raw
    $json = $raw | ConvertFrom-Json
    $serverCount = ($json.mcpServers.PSObject.Properties | Measure-Object).Count
    $serverNames = ($json.mcpServers.PSObject.Properties | Select-Object -ExpandProperty Name) -join ", "
    Write-Output ("mcp_config.json : VALID JSON ({0} servers: {1})" -f $serverCount, $serverNames)
  } catch {
    Write-Output ("mcp_config.json : INVALID JSON ({0})" -f $_.Exception.Message)
  }
} else {
  Write-Output "mcp_config.json : MISSING"
}
