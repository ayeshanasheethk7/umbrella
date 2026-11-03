import os
import json

targets = [
    'AGENTS.md',
    'GEMINI.md',
    '.agents/rules/01-design-system.md',
    '.agents/rules/02-security-privacy.md',
    '.agents/rules/03-typescript-nextjs.md',
    '.agents/rules/04-supabase-sql.md',
    'docs/SPEC.md',
    'docs/DECISIONS.md',
    'docs/PROGRESS.md',
    'docs/DB-RUNBOOK.md',
    'docs/DEPLOY.md',
    'docs/SWARM_COORDINATION.md',
    '.agents/skills/graphify/SKILL.md',
    '.agents/skills/subagent-handling/SKILL.md',
    '.agents/skills/umbrella-qr-card/SKILL.md',
    '.agents/skills/umbrella-supabase-rls/SKILL.md',
    '.agents/workflows/start-phase.md',
    '.agents/workflows/verify.md',
    '.agents/workflows/security-audit.md',
    '.agents/workflows/design-review.md',
    'PROJECT.md'
]

print(f"{'Target File':<45} | {'Length':>6} chars | {'Status':>6}")
print("-" * 65)

all_under_12k = True
for t in targets:
    if os.path.exists(t):
        with open(t, 'r', encoding='utf-8') as f:
            data = f.read()
        l = len(data)
        ok = l < 12000
        if not ok:
            all_under_12k = False
        print(f"{t:<45} | {l:>6} chars | {'PASS' if ok else 'FAIL (>12k)'}")
    else:
        all_under_12k = False
        print(f"{t:<45} | MISSING      | FAIL")

print("-" * 65)
print(f"Overall 12,000 character limit result: {'PASS' if all_under_12k else 'FAIL'}")

# Check MCP files
mcp_files = [
    r'C:\Users\DELL\.gemini\config\mcp_config.json',
    r'.gemini\mcp_config.json'
]
print("\n=== MCP Config Audit ===")
for m in mcp_files:
    if os.path.exists(m):
        try:
            with open(m, 'r', encoding='utf-8') as f:
                c = json.load(f)
            servers = list(c.get('mcpServers', {}).keys())
            print(f"{m} : VALID JSON ({len(servers)} servers: {', '.join(servers)})")
        except Exception as e:
            print(f"{m} : INVALID JSON: {e}")
    else:
        print(f"{m} : MISSING")
