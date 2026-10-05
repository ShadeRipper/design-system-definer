# Installs the skill for Claude Code (personal scope): ~\.claude\skills\design-system-definer
$ErrorActionPreference = 'Stop'
$src  = Join-Path $PSScriptRoot 'skills\design-system-definer'
$root = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME '.claude\skills' }
$dest = Join-Path $root 'design-system-definer'
New-Item -ItemType Directory -Force -Path $root | Out-Null
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Copy-Item -Recurse $src $dest
Get-ChildItem $dest -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Write-Host "Installed to $dest. Restart Claude Code, then ask: 'help me define a design system'."
