#!/usr/bin/env python3
"""
Export chat sessions from Hermes, Claude Code, and Codex as dialogue Markdown.

Self-contained — only needs Python 3.8+ standard library.

Usage:
  python3 export_chat.py                        # auto-detect, export most recent from all
  python3 export_chat.py --tool hermes          # specific tool
  python3 export_chat.py --tool claude          # all Claude sessions
  python3 export_chat.py --tool codex           # all Codex sessions
  python3 export_chat.py --tool all             # everything combined
  python3 export_chat.py --recent 5             # last 5 sessions (all tools)
  python3 export_chat.py --session-id <id>      # specific session
  python3 export_chat.py --output ~/backup.md   # custom output path
  python3 export_chat.py --list                 # list available sessions
"""

import argparse
import glob
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))
DEFAULT_DESKTOP = "/mnt/c/Users/12174/Desktop"

# ─── Helpers ──────────────────────────────────────────────────────────────

def fmt_ts(ts):
    """Unix timestamp or ISO string → readable CST datetime."""
    if not ts:
        return "未知时间"
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return ts
    else:
        dt = datetime.fromtimestamp(ts, tz=CST)
    return dt.astimezone(CST).strftime("%Y-%m-%d %H:%M:%S")


def default_output_path():
    desktop = DEFAULT_DESKTOP
    if not os.path.isdir(desktop):
        desktop = os.path.expanduser("~/Desktop")
    if not os.path.isdir(desktop):
        desktop = "."
    ts = datetime.now(CST).strftime("%Y%m%d_%H%M%S")
    return os.path.join(desktop, f"对话记录_{ts}.md")


def save_file(content, path):
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ─── Dialogue Formatter ──────────────────────────────────────────────────

def format_dialogue(session_data, include_tools=False):
    """Generic session dict → dialogue Markdown."""
    messages = session_data.get("messages", [])
    meta = session_data.get("meta", {})

    lines = ["# 对话记录", ""]
    if meta.get("title"):
        lines.append(f"**标题:** {meta['title']}")
    lines.append(f"**日期:** {meta.get('started', '未知')}")
    if meta.get("tool"):
        lines.append(f"**工具:** {meta['tool']}")
    if meta.get("session_id"):
        lines.append(f"**Session ID:** {meta['session_id']}")
    if meta.get("model"):
        lines.append(f"**模型:** {meta['model']}")
    lines += ["", "---", ""]

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "user":
            if content and not content.startswith("[System:"):
                lines.append(f"**👤 用户:** {content}")
                lines.append("")
        elif role == "assistant":
            if content:
                lines.append(f"**🤖 助手:** {content}")
                lines.append("")
            elif include_tools:
                tools = msg.get("tool_calls", [])
                if tools:
                    names = [t.get("function", {}).get("name", "?") for t in tools]
                    lines.append(f"**🤖 助手:** [调用工具: {', '.join(names)}]")
                    lines.append("")
        elif role == "tool" and include_tools:
            name = msg.get("tool_name", "unknown")
            preview = (content[:200] + "...") if content and len(content) > 200 else content
            lines.append(f"**🔧 [{name}]:** `{preview}`")
            lines.append("")

    return "\n".join(lines)


# ─── Hermes ───────────────────────────────────────────────────────────────

def hermes_list_sessions(count=10):
    """List recent Hermes sessions."""
    try:
        result = subprocess.run(
            ["hermes", "sessions", "list", "--limit", str(count)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return []
        sessions = []
        for line in result.stdout.strip().split("\n"):
            parts = line.strip().split()
            for p in parts:
                if len(p) > 10 and "_" in p and p[0].isdigit():
                    sessions.append({"id": p, "tool": "hermes"})
                    break
        return sessions
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def hermes_export_session(session_id):
    """Export a single Hermes session."""
    try:
        result = subprocess.run(
            ["hermes", "sessions", "export", "-", "--session-id", session_id],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout.strip().split("\n")[0])
        messages = []
        for msg in data.get("messages", []):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content or ""})
        return {
            "messages": messages,
            "meta": {
                "tool": "Hermes",
                "session_id": data.get("id", ""),
                "title": data.get("title", ""),
                "started": fmt_ts(data.get("started_at")),
                "source": data.get("source", ""),
            }
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


# ─── Claude Code ──────────────────────────────────────────────────────────

def claude_find_sessions():
    """Find all Claude Code session files."""
    claude_dir = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_dir):
        return []
    sessions = []
    for jsonl_path in glob.glob(os.path.join(claude_dir, "**", "*.jsonl"), recursive=True):
        # Skip subagent files
        if "/subagents/" in jsonl_path:
            continue
        sid = Path(jsonl_path).stem
        # Try to get timestamp from file
        try:
            mtime = os.path.getmtime(jsonl_path)
        except OSError:
            mtime = 0
        sessions.append({
            "id": sid,
            "tool": "claude",
            "path": jsonl_path,
            "mtime": mtime,
        })
    sessions.sort(key=lambda s: s["mtime"], reverse=True)
    return sessions


def claude_export_session(session_path):
    """Parse a Claude Code JSONL session into dialogue format."""
    messages = []
    session_id = Path(session_path).stem
    model = ""
    started = None

    with open(session_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")

            if entry_type == "user":
                msg = entry.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, list):
                    # Extract text from content blocks
                    texts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            texts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            texts.append(block)
                    content = "\n".join(texts)
                if content and not content.startswith("[System:"):
                    messages.append({"role": "user", "content": content})
                if not started:
                    ts = entry.get("timestamp")
                    if ts:
                        started = fmt_ts(ts)

            elif entry_type == "assistant":
                msg = entry.get("message", {})
                if not model:
                    model = msg.get("model", "")
                content_blocks = msg.get("content", [])
                if isinstance(content_blocks, str):
                    if content_blocks:
                        messages.append({"role": "assistant", "content": content_blocks})
                elif isinstance(content_blocks, list):
                    texts = []
                    for block in content_blocks:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                texts.append(block.get("text", ""))
                            elif block.get("type") == "tool_use":
                                pass  # skip tool calls in basic mode
                        elif isinstance(block, str):
                            texts.append(block)
                    combined = "\n".join(texts).strip()
                    if combined:
                        messages.append({"role": "assistant", "content": combined})

    return {
        "messages": messages,
        "meta": {
            "tool": "Claude Code",
            "session_id": session_id,
            "started": started or "未知",
            "model": model,
        }
    }


# ─── Codex ────────────────────────────────────────────────────────────────

def codex_find_sessions():
    """Find all Codex session rollout files."""
    codex_dir = os.path.expanduser("~/.codex/sessions")
    if not os.path.isdir(codex_dir):
        return []
    sessions = []
    for jsonl_path in glob.glob(os.path.join(codex_dir, "**", "rollout-*.jsonl"), recursive=True):
        filename = Path(jsonl_path).stem
        # Extract UUID from filename: rollout-YYYY-MM-DDTHH-MM-SS-<uuid>
        # UUID format: 8-4-4-4-12 hex chars (36 chars total)
        uuid_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$', filename)
        sid = uuid_match.group(1) if uuid_match else filename
        try:
            mtime = os.path.getmtime(jsonl_path)
        except OSError:
            mtime = 0
        sessions.append({
            "id": sid,
            "tool": "codex",
            "path": jsonl_path,
            "mtime": mtime,
        })
    sessions.sort(key=lambda s: s["mtime"], reverse=True)
    return sessions


def codex_export_session(session_path):
    """Parse a Codex rollout JSONL session into dialogue format."""
    messages = []
    session_id = ""
    model = ""
    started = None

    with open(session_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")
            payload = entry.get("payload", {})

            if entry_type == "session_meta":
                session_id = payload.get("id", "")
                ts = payload.get("timestamp")
                if ts:
                    started = fmt_ts(ts)

            elif entry_type == "response_item":
                ptype = payload.get("type", "")
                if ptype == "message":
                    role = payload.get("role", "")
                    content_items = payload.get("content", [])

                    if role == "user":
                        texts = []
                        for item in content_items:
                            if isinstance(item, dict) and item.get("type") == "input_text":
                                texts.append(item.get("text", ""))
                            elif isinstance(item, str):
                                texts.append(item)
                        combined = "\n".join(texts).strip()
                        # Skip system/env context messages
                        if combined and not combined.startswith("<environment_context>"):
                            messages.append({"role": "user", "content": combined})

                    elif role == "assistant":
                        texts = []
                        for item in content_items:
                            if isinstance(item, dict):
                                if item.get("type") == "output_text":
                                    texts.append(item.get("text", ""))
                                elif item.get("type") == "reasoning_text":
                                    pass  # skip reasoning
                            elif isinstance(item, str):
                                texts.append(item)
                        combined = "\n".join(texts).strip()
                        if combined:
                            messages.append({"role": "assistant", "content": combined})

            elif entry_type == "turn_context":
                collab = payload.get("collaboration_mode", {})
                settings = collab.get("settings", {})
                if not model:
                    model = settings.get("model", "")

    return {
        "messages": messages,
        "meta": {
            "tool": "Codex",
            "session_id": session_id,
            "started": started or "未知",
            "model": model,
        }
    }


# ─── Unified Interface ───────────────────────────────────────────────────

def list_all_sessions():
    """List sessions from all tools."""
    all_sessions = []

    # Hermes
    for s in hermes_list_sessions(20):
        all_sessions.append(s)

    # Claude
    for s in claude_find_sessions():
        all_sessions.append(s)

    # Codex
    for s in codex_find_sessions():
        all_sessions.append(s)

    return all_sessions


def export_by_tool(tool, session_id=None, recent=None):
    """Export sessions from a specific tool."""
    if tool == "hermes":
        if session_id:
            data = hermes_export_session(session_id)
            return [data] if data else []
        sessions = hermes_list_sessions(recent or 10)
        results = []
        for s in sessions:
            data = hermes_export_session(s["id"])
            if data:
                results.append(data)
        return results

    elif tool == "claude":
        sessions = claude_find_sessions()
        if session_id:
            for s in sessions:
                if s["id"].startswith(session_id):
                    return [claude_export_session(s["path"])]
            return []
        return [claude_export_session(s["path"]) for s in sessions[:recent or len(sessions)]]

    elif tool == "codex":
        sessions = codex_find_sessions()
        if session_id:
            for s in sessions:
                if s["id"].startswith(session_id):
                    return [codex_export_session(s["path"])]
            return []
        return [codex_export_session(s["path"]) for s in sessions[:recent or len(sessions)]]

    return []


def export_all_tools(recent_per_tool=1):
    """Export recent sessions from all tools."""
    results = []

    # Hermes
    hermes_sessions = hermes_list_sessions(recent_per_tool)
    for s in hermes_sessions[:recent_per_tool]:
        data = hermes_export_session(s["id"])
        if data:
            results.append(data)

    # Claude
    claude_sessions = claude_find_sessions()
    for s in claude_sessions[:recent_per_tool]:
        data = claude_export_session(s["path"])
        if data and data["messages"]:
            results.append(data)

    # Codex
    codex_sessions = codex_find_sessions()
    for s in codex_sessions[:recent_per_tool]:
        data = codex_export_session(s["path"])
        if data and data["messages"]:
            results.append(data)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Export chat sessions from Hermes/Claude Code/Codex as dialogue Markdown"
    )
    parser.add_argument("--tool", "-t", choices=["hermes", "claude", "codex", "all"],
                        default="all", help="Which tool to export from (default: all)")
    parser.add_argument("--session-id", "-s", help="Export a specific session ID")
    parser.add_argument("--recent", "-r", type=int, nargs="?", const=1,
                        help="Export N most recent sessions per tool (default: 1)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--tools-calls", action="store_true", help="Include tool calls")
    parser.add_argument("--list", "-l", action="store_true", help="List available sessions")

    args = parser.parse_args()

    # List mode
    if args.list:
        sessions = list_all_sessions()
        if not sessions:
            print("没有找到任何会话。")
            return
        print(f"{'工具':<12} {'Session ID':<40} {'来源/路径'}")
        print("-" * 90)
        for s in sessions:
            tool = s.get("tool", "?")
            sid = s.get("id", "?")[:38]
            extra = s.get("path", s.get("source", ""))
            print(f"{tool:<12} {sid:<40} {extra}")
        return

    # Default: export most recent
    if args.recent is None and not args.session_id:
        args.recent = 1

    output = args.output or default_output_path()

    # Export
    if args.session_id:
        # Try each tool
        for tool_name in ["hermes", "claude", "codex"]:
            results = export_by_tool(tool_name, args.session_id)
            if results:
                break
        else:
            print(f"ERROR: Session '{args.session_id}' not found in any tool.", file=sys.stderr)
            sys.exit(1)
    elif args.tool == "all":
        results = export_all_tools(args.recent or 1)
    else:
        results = export_by_tool(args.tool, recent=args.recent)

    if not results:
        print("ERROR: No sessions found.", file=sys.stderr)
        sys.exit(1)

    # Format
    parts = []
    for i, data in enumerate(results):
        if i > 0:
            parts.append("\n\n" + "=" * 60 + "\n\n")
        parts.append(format_dialogue(data, include_tools=args.tools_calls))

    md = "\n".join(parts)
    path = save_file(md, output)

    msg_count = sum(len(d.get("messages", [])) for d in results)
    print(f"✅ 导出成功: {path}")
    print(f"   会话数: {len(results)}, 总消息数: {msg_count}")
    print(f"   文件大小: {os.path.getsize(path):,} bytes")


if __name__ == "__main__":
    main()
