#!/usr/bin/env bash
# Lightweight pattern-based secret scan for CI. Scans git-tracked files (excluding
# lockfiles) for common hardcoded credential shapes. Not a replacement for GitHub's
# built-in Secret Scanning (repo Settings > Code security) — enable that too.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

FILES=$(git ls-files | grep -vE '^(package-lock\.json|.*\.lock)$')

PATTERNS=(
  'AIza[0-9A-Za-z_-]{35}'                     # Google API key
  'AKIA[0-9A-Z]{16}'                          # AWS access key id
  'xox[baprs]-[0-9A-Za-z-]{10,}'              # Slack token
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'        # PEM private key
  '(?i)(api[_-]?key|secret|token|password)[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9_\-]{16,}["'"'"']'
)

FOUND=0

for pattern in "${PATTERNS[@]}"; do
  matches=$(echo "$FILES" | xargs -r grep -InE "$pattern" -- 2>/dev/null | \
    grep -viE 'YOUR_API_KEY|PLACEHOLDER|process\.env|os\.environ|getenv|secrets\.|\$\{\{' || true)
  if [ -n "$matches" ]; then
    echo "❌ Potential secret matched pattern: $pattern"
    echo "$matches" | sed 's/^/   /'
    FOUND=1
  fi
done

if [ "$FOUND" -eq 1 ]; then
  echo ""
  echo "Secret scan failed. Remove hardcoded credentials and read from environment variables / repository secrets instead."
  exit 1
fi

echo "✅ No hardcoded secrets found by pattern scan."
