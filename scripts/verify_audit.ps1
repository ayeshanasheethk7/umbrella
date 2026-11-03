$files = @(
  'AGENTS.md',
  'GEMINI.md',
  '.agents\rules\01-design-system.md',
  '.agents\rules\02-security-privacy.md',
  '.agents\rules\03-typescript-nextjs.md',
  '.agents\rules\04-supabase-sql.md',
  'docs\SPEC.md',
  'docs\DECISIONS.md',
  'docs\PROGRESS.md',
  'docs\DB-RUNBOOK.md',
  'docs\DEPLOY.md',
  'docs\SWARM_COORDINATION.md',
  '.agents\skills\graphify\SKILL.md',
  '.agents\skills\subagent-handling\SKILL.md',
  'PROJECT.md'
)

$base = "c:\Users\DELL\ayesha_pro\medi_qr"
$results = foreach ($f in $files) {
  $p = Join-Path $base $f
  if (Test-Path $p) {
    $content = Get-Content -Path $p -Raw
    [PSCustomObject]@{
      File = $f
      Length = $content.Length
      Lines = ($content -split "`r?`n").Count
      Under12k = ($content.Length -lt 12000)
    }
  } else {
    [PSCustomObject]@{
      File = $f
      Length = -1
      Lines = 0
      Under12k = $false
    }
  }
}

$results | Format-Table -AutoSize
