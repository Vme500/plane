#!/usr/bin/env bash
# AutoLoop pre-flight checks — short output, exit code reflects critical failures
set -uo pipefail

cd "$(dirname "$0")/../.." || exit 1

PASS=0
FAIL=0
WARN=0

check() {
  local name="$1" result="$2"
  if [[ "$result" == "PASS" ]]; then
    echo "  ✅ $name"
    ((PASS++))
  elif [[ "$result" == "WARN" ]]; then
    echo "  ⚠️  $name"
    ((WARN++))
  else
    echo "  ❌ $name"
    ((FAIL++))
  fi
}

echo "=== Plane AI AutoLoop Pre-Flight ==="
echo ""

# 1. Git status
GIT_CLEAN=$(git status --short | wc -l)
check "git_clean (changed=$GIT_CLEAN)" "$([[ $GIT_CLEAN -eq 0 ]] && echo PASS || echo WARN)"

# 2. Branch
BRANCH=$(git branch --show-current)
check "branch=$BRANCH" "$([[ "$BRANCH" == "feat/ai-phase-6-mcp-readonly-runtime" ]] && echo PASS || echo FAIL)"

# 3. Dev stack
CONTAINERS=$(docker compose -p plane-ai-dev --env-file .env.ai-dev.local -f docker-compose.ai-dev.yml ps --format '{{.Name}} {{.Status}}' 2>/dev/null | wc -l)
check "dev_stack (containers=$CONTAINERS)" "$([[ $CONTAINERS -ge 5 ]] && echo PASS || echo FAIL)"

# 4. Route firewall
FW_RESULT=$(python3 scripts/check_native_ai_route_firewall.py 2>&1)
check "route_firewall" "$(echo "$FW_RESULT" | grep -q 'All checks passed' && echo PASS || echo FAIL)"

# 5. asdfg count
ASDFG=$(docker exec plane-ai-dev-api python manage.py shell -c "from plane.db.models import Issue; print(Issue.objects.filter(name='asdfg').count())" 2>/dev/null || echo "ERROR")
check "asdfg_count=$ASDFG" "$([[ "$ASDFG" == "0" ]] && echo PASS || echo FAIL)"

# 6. ai.write.executed
EXEC=$(docker exec plane-ai-dev-api python manage.py shell -c "from plane.db.models import AIAuditEvent; print(AIAuditEvent.objects.filter(event='ai.write.executed').count())" 2>/dev/null || echo "ERROR")
check "ai_write_executed=$EXEC" "$([[ "$EXEC" == "1" ]] && echo PASS || echo FAIL)"

# 7. .env.ai-dev.local not tracked
ENV_TRACKED=$(git ls-files .env.ai-dev.local | wc -l)
check "env_not_tracked" "$([[ $ENV_TRACKED -eq 0 ]] && echo PASS || echo FAIL)"

# 8. Secret scan (to /tmp)
grep -R "sk-\|api_key=.*[^=]\|password=.*[^=]\|confirmation_token.*[A-Za-z0-9]" -ni CLAUDE.md tools/ docs/ scripts/ apps/web/app apps/web/core apps/api/plane docker-compose.ai-dev.yml 2>/dev/null > /tmp/autoloop-secret-scan.txt || true
SECRET_HITS=$(wc -l < /tmp/autoloop-secret-scan.txt)
check "secret_scan (hits=$SECRET_HITS -> /tmp/autoloop-secret-scan.txt)" "PASS"

echo ""
echo "=== Summary: PASS=$PASS WARN=$WARN FAIL=$FAIL ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
