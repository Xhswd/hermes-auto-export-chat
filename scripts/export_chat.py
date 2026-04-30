#!/usr/bin/env python3
"""
Export Hermes Agent chat sessions as readable dialogue-format Markdown.

Self-contained: only needs `hermes` CLI on PATH, no hermes-agent imports.

Usage:
  python3 export_chat.py --recent 1 [--output path.md]
  python3 export_chat.py --session-id <id> [--output path.md]
  python3 export_chat.py --all [--output path.md]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
DEFAULT_DESKTOP = "/mnt/c/Users/12174/Desktop"


def run_hermes(*args):
    """Run a hermes CLI command and return stdout."""
    cmd = ["hermes"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"ERROR: hermes {' '.join(args)} failed: {result.stderr.strip()}", file=sys.stderr)
            return None
        return result.stdout
    except FileNotFoundError:
        print("ERROR: 'hermes' not found on PATH. Is Hermes Agent installed?", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: hermes command timed out.", file=sys.stderr)
        sys.exit(1)


def get_recent_sessions(count=5):
    """Get recent session IDs via hermes sessions list."""
    output = run_hermes("sessions", "list", "--limit", str(count))
    if not output:
        return []
    # Parse the table output — session IDs are the last column
    sessions = []
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("Title") or line.startswith("-") or line.startswith("─"):
            continue
        # Session ID is typically the last token (format: YYYYMMDD_HHMMSS_xxxxxx)
        parts = line.split()
        for part in parts:
            if len(part) > 10 and "_" in part and part[0].isdigit():
                sessions.append(part)
                break
    return sessions


def export_session_jsonl(session_id):
    """Export a single session via hermes sessions export to stdout."""
    output = run_hermes("sessions", "export", "-", "--session-id", session_id)
    if not output:
        return None
    try:
        return json.loads(output.strip().split("\n")[0])
    except (json.JSONDecodeError, IndexError):
        return None


def export_all_jsonl():
    """Export all sessions via hermes sessions export to stdout."""
    output = run_hermes("sessions", "export", "-")
    if not output:
        return []
    sessions = []
    for line in output.strip().split("\n"):
        if line.strip():
            try:
                sessions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return sessions


def format_timestamp(ts):
    """Convert unix timestamp to readable datetime string in CST."""
    if not ts:
        return "未知时间"
    dt = datetime.fromtimestamp(ts, tz=CST)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_dialogue(session_data, include_tools=False):
    """Format a session as a dialogue Markdown document."""
    messages = session_data.get("messages", [])
    session_id = session_data.get("id", "unknown")
    source = session_data.get("source", "unknown")
    title = session_data.get("title", "")
    started = format_timestamp(session_data.get("started_at"))
    last_active = format_timestamp(session_data.get("last_active"))

    lines = []
    lines.append("# 对话记录")
    lines.append("")
    if title:
        lines.append(f"**标题:** {title}")
    lines.append(f"**日期:** {started}")
    lines.append(f"**最后活跃:** {last_active}")
    lines.append(f"**Session ID:** {session_id}")
    lines.append(f"**来源:** {source}")
    lines.append("")
    lines.append("---")
    lines.append("")

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
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    tool_names = [tc.get("function", {}).get("name", "?") for tc in tool_calls]
                    lines.append(f"**🤖 助手:** [调用工具: {', '.join(tool_names)}]")
                    lines.append("")
        elif role == "tool" and include_tools:
            tool_name = msg.get("tool_name", "unknown")
            preview = (content[:200] + "...") if content and len(content) > 200 else content
            lines.append(f"**🔧 工具 [{tool_name}]:** `{preview}`")
            lines.append("")

    return "\n".join(lines)


def default_output_path():
    """Generate default output path on Windows Desktop."""
    desktop = DEFAULT_DESKTOP
    if not os.path.isdir(desktop):
        home_desktop = os.path.expanduser("~/Desktop")
        desktop = home_desktop if os.path.isdir(home_desktop) else "."

    ts = datetime.now(CST).strftime("%Y%m%d_%H%M%S")
    return os.path.join(desktop, f"对话记录_{ts}.md")


def save_markdown(content, output_path):
    """Write markdown content to file, creating dirs if needed."""
    output_path = os.path.expanduser(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Export Hermes chat sessions as dialogue Markdown")
    parser.add_argument("--session-id", "-s", help="Export a specific session")
    parser.add_argument("--all", "-a", action="store_true", help="Export all sessions")
    parser.add_argument("--recent", "-r", type=int, nargs="?", const=5,
                        help="Export N most recent sessions (default: 5)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--tools", "-t", action="store_true", help="Include tool calls")

    args = parser.parse_args()

    # Default: export most recent session
    if not args.session_id and not args.all and args.recent is None:
        args.recent = 1

    output = args.output or default_output_path()

    if args.all:
        sessions = export_all_jsonl()
        if not sessions:
            print("ERROR: No sessions found.", file=sys.stderr)
            sys.exit(1)
        parts = []
        for i, s in enumerate(sessions):
            if i > 0:
                parts.append("\n\n" + "=" * 60 + "\n\n")
            parts.append(format_dialogue(s, include_tools=args.tools))
        md = "\n".join(parts)
        path = save_markdown(md, output)
        print(f"✅ 导出成功: {path}")
        print(f"   会话数: {len(sessions)}")
        print(f"   文件大小: {os.path.getsize(path):,} bytes")

    elif args.recent is not None:
        session_ids = get_recent_sessions(args.recent)
        if not session_ids:
            print("ERROR: No sessions found.", file=sys.stderr)
            sys.exit(1)
        parts = []
        count = 0
        for i, sid in enumerate(session_ids):
            data = export_session_jsonl(sid)
            if not data:
                continue
            if count > 0:
                parts.append("\n\n" + "=" * 60 + "\n\n")
            parts.append(format_dialogue(data, include_tools=args.tools))
            count += 1
        if count == 0:
            print("ERROR: Could not export any sessions.", file=sys.stderr)
            sys.exit(1)
        md = "\n".join(parts)
        path = save_markdown(md, output)
        print(f"✅ 导出成功: {path}")
        print(f"   会话数: {count}")
        print(f"   文件大小: {os.path.getsize(path):,} bytes")

    elif args.session_id:
        data = export_session_jsonl(args.session_id)
        if not data:
            print(f"ERROR: Session '{args.session_id}' not found.", file=sys.stderr)
            sys.exit(1)
        md = format_dialogue(data, include_tools=args.tools)
        path = save_markdown(md, output)
        msg_count = len(data.get("messages", []))
        print(f"✅ 导出成功: {path}")
        print(f"   消息数: {msg_count}")
        print(f"   文件大小: {os.path.getsize(path):,} bytes")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
