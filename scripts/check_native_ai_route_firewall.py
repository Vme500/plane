#!/usr/bin/env python3
"""
Route firewall check: ensure Native AI does not depend on legacy pi-ai code.

Exit 0 = all checks pass.
Exit 1 = violations found.
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files that are part of the native AI route
NATIVE_AI_BACKEND = [
    "apps/api/plane/app/views/ai_native.py",
    "apps/api/plane/ai/mcp_gateway.py",
    "apps/api/plane/ai/mcp_config.py",
    "apps/api/plane/ai/official_mcp_client.py",
]

NATIVE_AI_FRONTEND = [
    "apps/web/core/components/workspace/sidebar/ai-assistant-drawer.tsx",
    "apps/web/core/services/native-ai.service.ts",
]

# Legacy modules that native AI must NOT import (exact import patterns)
LEGACY_IMPORTS = [
    "from plane.ai.mcp_runtime import",
    "from plane.ai import mcp_runtime",
    "import plane.ai.mcp_runtime",
]

# Legacy frontend patterns (exact patterns to avoid false positives)
LEGACY_FRONTEND_PATTERNS = [
    "new AIService()",
    ".createGptTask(",
    "/ai-test/pi-chat",
]

violations = []


def check_file(filepath, forbidden_patterns, description):
    """Check if a file contains forbidden patterns."""
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        return

    with open(full_path, "r") as f:
        content = f.read()
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in forbidden_patterns:
                if pattern in line:
                    # Skip comments
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("//"):
                        continue
                    violations.append(
                        f"  VIOLATION: {filepath}:{i}: found '{pattern}'\n    {stripped}"
                    )


def check_source_in_response(filepath):
    """Check that native endpoint returns source=official_mcp_gateway."""
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        return

    with open(full_path, "r") as f:
        content = f.read()
        if '"source": "official_mcp_gateway"' not in content and "'source': 'official_mcp_gateway'" not in content:
            violations.append(
                f"  VIOLATION: {filepath}: native endpoint does not return source=official_mcp_gateway"
            )


def check_source_validation_in_frontend(filepath):
    """Check that frontend validates source=official_mcp_gateway."""
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        return

    with open(full_path, "r") as f:
        content = f.read()
        if "official_mcp_gateway" not in content:
            violations.append(
                f"  VIOLATION: {filepath}: frontend does not validate source=official_mcp_gateway"
            )


def main():
    print("=== Native AI Route Firewall Check ===\n")

    # Check native backend files don't import legacy
    print("Checking native backend files for legacy imports...")
    for f in NATIVE_AI_BACKEND:
        check_file(f, LEGACY_IMPORTS, "legacy import")

    # Check native frontend files don't use legacy patterns
    print("Checking native frontend files for legacy patterns...")
    for f in NATIVE_AI_FRONTEND:
        check_file(f, LEGACY_FRONTEND_PATTERNS, "legacy pattern")

    # Check native endpoint returns source
    print("Checking native endpoint returns source=official_mcp_gateway...")
    check_source_in_response("apps/api/plane/app/views/ai_native.py")

    # Check frontend validates source
    print("Checking frontend validates source...")
    check_source_validation_in_frontend(
        "apps/web/core/components/workspace/sidebar/ai-assistant-drawer.tsx"
    )

    if violations:
        print(f"\n❌ {len(violations)} violation(s) found:\n")
        for v in violations:
            print(v)
        print("\nFix violations before committing.")
        sys.exit(1)
    else:
        print("\n✅ All checks passed. Native AI route is isolated from legacy.")
        sys.exit(0)


if __name__ == "__main__":
    main()
