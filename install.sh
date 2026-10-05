#!/usr/bin/env sh
# Installs the skill for Claude Code (personal scope): ~/.claude/skills/design-system-definer
set -e
src="$(cd "$(dirname "$0")" && pwd)/skills/design-system-definer"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/design-system-definer"
mkdir -p "$(dirname "$dest")"
rm -rf "$dest"
cp -R "$src" "$dest"
find "$dest" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "Installed to $dest. Restart Claude Code, then ask: 'help me define a design system'."
