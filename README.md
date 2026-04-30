# hermes-auto-export-chat

通用聊天记录导出工具 — 支持 **Hermes**、**Claude Code**、**Codex** 三个 Agent

导出为对话模式 (Q&A) Markdown 文档，保存到 Windows 桌面。

## 安装

```bash
git clone https://github.com/Xhswd/hermes-auto-export-chat.git /tmp/hermes-auto-export-chat
mkdir -p ~/.hermes/skills/productivity/
cp -r /tmp/hermes-auto-export-chat ~/.hermes/skills/productivity/auto-export-chat
rm -rf /tmp/hermes-auto-export-chat
```

## 用法

```bash
SCRIPT=~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py

# 列出所有工具的会话
python3 $SCRIPT --list

# 导出所有工具最近 1 个对话
python3 $SCRIPT --recent 1

# 只导 Hermes
python3 $SCRIPT --tool hermes --recent 1

# 只导 Claude Code
python3 $SCRIPT --tool claude --recent 1

# 只导 Codex
python3 $SCRIPT --tool codex --recent 1

# 导出指定 session
python3 $SCRIPT --session-id <id>

# 导出全部备份
python3 $SCRIPT --tool all --recent 999 --output ~/backup.md

# 自定义输出路径
python3 $SCRIPT --output ~/Desktop/对话.md
```

## 支持的工具

| 工具 | 存储路径 | 说明 |
|------|---------|------|
| Hermes | `~/.hermes/state.db` | 通过 `hermes sessions export` CLI |
| Claude Code | `~/.claude/projects/**/*.jsonl` | 直接解析 JSONL |
| Codex | `~/.codex/sessions/**/*.jsonl` | 直接解析 JSONL |

## 输出示例

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

## 依赖

- Python 3.8+
- Hermes CLI（仅导出 Hermes 会话时需要）

## License

MIT
