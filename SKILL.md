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

Export Hermes Agent chat sessions as readable dialogue-format Markdown documents.
The user strongly prefers **对话模式** (Q&A dialogue style) over technical summaries.
Default save location: Windows Desktop (`/mnt/c/Users/12174/Desktop/`).

## When to Use

- User says "导出对话", "export chat", "保存对话", "导出聊天记录"
- User wants to save the current conversation as a file
- User wants to backup or review past sessions

## Quick Reference

| Action | Command |
|--------|---------|
| Export current session | Run the export script with current session ID |
| Export specific session | Run with `--session-id <id>` |
| Export all sessions | Run with `--all` |
| Custom output path | Run with `--output /path/to/file.md` |

## Step-by-Step Procedure

### 1. Export Current Session (most common)

When the user says "导出对话" without specifying which session:

```bash
# Get the current session ID from the environment
# ${HERMES_SESSION_ID} is automatically replaced by Hermes

# Run the export script
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --session-id "${HERMES_SESSION_ID}" \
  --output "/mnt/c/Users/12174/Desktop/对话记录_$(date +%Y%m%d_%H%M%S).md"
```

If `${HERMES_SESSION_ID}` is not available, use `session_search` (no query) to find
the most recent session, then export that.

### 2. Export with Custom Name

If the user provides a filename:

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --session-id "${HERMES_SESSION_ID}" \
  --output "/mnt/c/Users/12174/Desktop/用户指定的名称.md"
```

### 3. Export a Past Session

Use `session_search` to find the session, then:

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --session-id "<session_id>" \
  --output "/mnt/c/Users/12174/Desktop/对话记录_<topic>.md"
```

### 4. Export All Sessions (backup)

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py \
  --all \
  --output "/mnt/c/Users/12174/Desktop/全部对话备份_$(date +%Y%m%d).md"
```

## Output Format (对话模式)

The exported file uses Q&A dialogue format:

```markdown
# 对话记录

**日期:** 2026-05-01
**Session ID:** 20260501_020738_fe4466
**来源:** cli

---

**👤 用户:** 你好，帮我安装 ComfyUI

**🤖 助手:** 好的，让我先检查一下你的环境...

**👤 用户:** 装好了吗？

**🤖 助手:** 是的，已经安装完成！
```

- Tool calls are collapsed to a brief note (e.g. `[调用工具: terminal]`)
- Tool results are omitted unless they contain the assistant's visible response
- Only `user` and `assistant` (visible) messages are included
- Reasoning/thinking content is excluded

## Common Pitfalls

1. **Session ID not found.** If the current session just started, it may not have
   an ID yet. Use `session_search` to find recent sessions instead.

2. **Database is `state.db`, not `sessions.db`.** The actual DB file is
   `~/.hermes/state.db`. The script handles this automatically.

2. **CJK filename issues.** The script handles Chinese filenames correctly on
   WSL/Windows. No special encoding needed.

3. **Large sessions.** Sessions with 500+ messages may produce large files.
   The script handles this without issues.

4. **Desktop path.** The default path assumes Windows user `12174`.
   If the path doesn't exist, the script falls back to `~/Desktop/` or the
   current directory.

## Verification

After export, confirm:
- [ ] File exists at the output path
- [ ] File is readable (not empty)
- [ ] Format is dialogue style (Q&A), not JSON or technical summary
- [ ] User can open it on Windows Desktop
