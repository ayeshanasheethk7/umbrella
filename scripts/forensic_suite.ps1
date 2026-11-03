# Forensic Suite for Milestone 1 Deliverables
$ErrorActionPreference = "Stop"

Write-Output "================================================="
Write-Output "FORENSIC INTEGRITY AUDIT SUITE - MILESTONE 1"
Write-Output "================================================="

$failures = 0

# Check 1: MCP JSON Syntax
Write-Output "`n[CHECK 1] MCP Configuration JSON Syntax..."
$mcpPaths = @(
    "C:\Users\DELL\.gemini\config\mcp_config.json",
    "c:\Users\DELL\ayesha_pro\medi_qr\.gemini\mcp_config.json"
)
foreach ($p in $mcpPaths) {
    if (Test-Path $p) {
        try {
            $raw = Get-Content -Path $p -Raw
            $json = $raw | ConvertFrom-Json
            $servers = ($json.mcpServers.PSObject.Properties | Select-Object -ExpandProperty Name)
            if ($servers -contains "memory" -and $servers -contains "supabase" -and $servers -contains "vercel") {
                Write-Output "  PASS: $p (Valid JSON, 3 servers: $($servers -join ', '))"
            } else {
                Write-Output "  FAIL: $p missing required servers ($($servers -join ', '))"
                $failures++
            }
        } catch {
            Write-Output "  FAIL: $p invalid JSON ($($_.Exception.Message))"
            $failures++
        }
    } else {
        Write-Output "  FAIL: $p does not exist"
        $failures++
    }
}

# Check 2: Character limits (<12,000 characters)
Write-Output "`n[CHECK 2] Character Limit Verification (<12,000 chars)..."
$targetFiles = @(
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
foreach ($f in $targetFiles) {
    $full = Join-Path $base $f
    if (Test-Path $full) {
        $content = Get-Content -Path $full -Raw
        $len = $content.Length
        if ($len -lt 12000) {
            Write-Output ("  PASS: {0,-40} Length: {1,5} chars (<12k)" -f $f, $len)
        } else {
            Write-Output ("  FAIL: {0,-40} Length: {1,5} chars (EXCEEDS 12k!)" -f $f, $len)
            $failures++
        }
    } else {
        Write-Output ("  FAIL: {0,-40} MISSING" -f $f)
        $failures++
    }
}

# Check 3: docs/SPEC.md formatting repairs from UMBRELLA_BUILD_KIT.md §1.6
Write-Output "`n[CHECK 3] docs/SPEC.md Formatting Repairs..."
$specContent = Get-Content -Path (Join-Path $base "docs\SPEC.md") -Raw
if ($specContent -match '```css\r?\n:root') {
    Write-Output "  PASS: CSS design tokens wrapped in ```css fence"
} else {
    Write-Output "  FAIL: CSS design tokens NOT wrapped in ```css fence"
    $failures++
}

if ($specContent -match '```text\r?\nsrc/') {
    Write-Output "  PASS: Directory tree wrapped in ```text fence"
} else {
    Write-Output "  FAIL: Directory tree NOT wrapped in ```text fence"
    $failures++
}

# Check for stray 's' before CSS block
if ($specContent -match '\r?\ns\r?\n```css') {
    Write-Output "  FAIL: Stray 's' detected before CSS block"
    $failures++
} else {
    Write-Output "  PASS: No stray 's' before CSS block"
}

# Check 4: Skill YAML Frontmatter
Write-Output "`n[CHECK 4] Skill YAML Frontmatter..."
$skills = @(
    ".agents\skills\graphify\SKILL.md",
    ".agents\skills\subagent-handling\SKILL.md"
)
foreach ($s in $skills) {
    $skillContent = Get-Content -Path (Join-Path $base $s) -Raw
    if ($skillContent -match '^---\r?\nname:\s*\S+\r?\ndescription:\s*\S+') {
        Write-Output "  PASS: $s has valid YAML frontmatter"
    } else {
        Write-Output "  FAIL: $s invalid or missing YAML frontmatter"
        $failures++
    }
}

# Check 5: Secret Key Leaks (N4: No real secrets or JWTs)
Write-Output "`n[CHECK 5] Secret Leak Audit..."
$jwtPattern = 'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'
$allFiles = Get-ChildItem -Path $base -Recurse -File | Where-Object { 
    $_.FullName -notmatch '\\\.git\\' -and 
    $_.FullName -notmatch '\\node_modules\\' 
}

$leaks = 0
foreach ($file in $allFiles) {
    $c = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($c -and $c -match $jwtPattern) {
        Write-Output "  FAIL: Secret JWT detected in $($file.FullName)"
        $leaks++
    }
}

if ($leaks -eq 0) {
    Write-Output "  PASS: Zero real JWT / secret key tokens detected across entire repository"
} else {
    Write-Output "  FAIL: $leaks Secret JWT tokens detected"
    $failures += $leaks
}

# Check 6: Facade & Placeholder Detection
Write-Output "`n[CHECK 6] Facade / Dummy Placeholder Detection..."
$suspiciousTerms = @("TODO:", "FIXME:", "LOREM IPSUM", "COMING SOON", "PLACEHOLDER IMPLEMENTATION")
$facades = 0
foreach ($f in $targetFiles) {
    $full = Join-Path $base $f
    $c = Get-Content -Path $full -Raw
    foreach ($term in $suspiciousTerms) {
        if ($c -match [regex]::Escape($term)) {
            Write-Output "  WARNING/FLAG: Found '$term' in $f"
            $facades++
        }
    }
}
if ($facades -eq 0) {
    Write-Output "  PASS: Zero facade / dummy placeholder flags detected in target deliverables"
} else {
    Write-Output "  TOTAL SUSPICIOUS OCCURRENCES: $facades"
}

Write-Output "`n================================================="
Write-Output "AUDIT SUMMARY: $failures FAILURE(S) DETECTED"
Write-Output "================================================="
if ($failures -eq 0) {
    Write-Output "VERDICT: CLEAN"
} else {
    Write-Output "VERDICT: INTEGRITY VIOLATION"
}
