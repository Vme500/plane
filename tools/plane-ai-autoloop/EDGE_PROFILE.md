# Dedicated Edge Profile Rules

## Profile Path

```
%LOCALAPPDATA%\Microsoft\Edge\User Data\PlaneAI-MCP-Test
```

## CDP Port

- Default: `9223`
- Fallback: `9224`

## Launch Command

```powershell
$profilePath = Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data\PlaneAI-MCP-Test'
Start-Process msedge -ArgumentList @(
  '--remote-debugging-port=9223',
  ('--user-data-dir=' + $profilePath),
  '--no-first-run',
  '--new-window',
  'http://localhost:18181/ai-test/projects'
)
```

## Rules

1. **Never commit** the profile directory, cookies, sessions, or screenshots
2. **Never output** cookies, sessions, or auth tokens
3. **First login** — user completes manually in dedicated Edge Profile
4. **Confirm click** — only in 9.5C with explicit user approval
5. **CDP from WSL** — may be blocked; use PowerShell fallback or ask user for manual steps

## WSL→Windows CDP Limitation

WSL cannot connect to Windows localhost CDP port directly. Options:

- Run Playwright from Windows (requires Node.js on Windows)
- Use PowerShell CDP scripts
- Ask user for manual browser interaction
