---
name: auto-export-chat
description: "Use when the user wants to export or save a chat/conversation. Exports Hermes sessions as readable dialogue documents (对话模式) to the Windows Desktop."
version: 1.0.0
author: User
license: MIT
metadata:
  hermes:
    tags: [export, chat, dialogue, session, backup, 导出, 对话]
    related_skills: []
---

# Auto Export Chat (自动导出对话)

## Overview

Export chat sessions from **Hermes**, **Claude Code**, and **Codex** as readable
dialogue-format Markdown documents. Self-contained Python script, no dependencies
beyond Python 3.8+ stdlib.

Default save location: Windows Desktop (`/mnt/c/Users/12174/Desktop/`).

## When to Use

- User says "导出对话", "export chat", "保存对话", "导出聊天记录"
- User wants to save the current conversation as a file
- User wants to backup sessions from Hermes, Claude Code, or Codex
- User wants to review past sessions across all tools

## Quick Reference

| Action | Command |
|--------|---------|
| Export most recent (all tools) | `--recent 1` |
| Export from specific tool | `--tool hermes\|claude\|codex\|all` |
| Export specific session | `--session-id <id>` |
| List all sessions | `--list` |
| Custom output path | `--output /path/to/file.md` |
| Include tool calls | `--tools-calls` |

## Step-by-Step Procedure

### 1. Export Current Session (most common)

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --recent 1 \
  --output "/mnt/c/Users/12174/Desktop/对话记录_$(date +%Y%m%d_%H%M%S).md"
```

This auto-detects the most recent session from all tools (Hermes, Claude, Codex).

### 2. Export from a Specific Tool

```bash
# Hermes only
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --tool hermes --recent 1

# Claude Code only
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --tool claude --recent 1

# Codex only
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --tool codex --recent 1
```

### 3. List All Available Sessions

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py --list
```

### 4. Export a Specific Session by ID

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --session-id "20260501_021329_69e93b"
```

### 5. Export All Sessions (backup)

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --tool all --recent 999 \
  --output "/mnt/c/Users/12174/Desktop/全部对话备份_$(date +%Y%m%d).md"
```

## Supported Tools

| Tool | Storage Location | Detection |
|------|-----------------|-----------|
| Hermes | `~/.hermes/state.db` | `hermes sessions export` CLI |
| Claude Code | `~/.claude/projects/**/*.jsonl` | Direct JSONL parsing |
| Codex | `~/.codex/sessions/**/*.jsonl` | Direct JSONL parsing |

## Output Format (对话模式)

```markdown
# 对话记录

**工具:** Claude Code
**日期:** 2026-04-28 17:01:35
**Session ID:** 8cc13c39-4358-482b-827f-5461d97a8163
**模型:** claude-sonnet-4

---

**👤 用户:** 你好

**🤖 助手:** 你好！有什么可以帮你的？
```

## Common Pitfalls

1. **Session ID not found.** Use `--list` to see all available sessions across all tools.

2. **Database is `state.db`, not `sessions.db`.** The script handles this automatically.

3. **Desktop path.** Default assumes Windows user `12174`. Adjust if needed.

4. **Claude Code subagent sessions** are automatically excluded from the listing.

5. **Codex UUID parsing.** The script correctly extracts full UUIDs from rollout filenames.

## Verification

After export, confirm:
- [ ] File exists at the output path
- [ ] File is readable (not empty)
- [ ] Format is dialogue style (Q&A), not JSON or technical summary
- [ ] User can open it on Windows Desktop
