# hermes-auto-export-chat

Hermes Agent Skill — 自动导出聊天记录为对话格式 Markdown 文档

## 功能

- 导出当前/指定/全部 session 为可读的对话记录
- 对话模式（Q&A 格式），不是技术摘要
- 自动保存到 Windows 桌面
- 支持中文

## 安装

```bash
git clone https://github.com/Xhswd/hermes-auto-export-chat.git /tmp/hermes-auto-export-chat
mkdir -p ~/.hermes/skills/productivity/
cp -r /tmp/hermes-auto-export-chat ~/.hermes/skills/productivity/auto-export-chat
rm -rf /tmp/hermes-auto-export-chat
```

安装后重启 Hermes，对 agent 说"导出对话"即可触发。

## 命令行用法

```bash
# 导出最近 1 个 session（默认）
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py

# 导出最近 N 个
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py --recent 5

# 导出指定 session
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py --session-id <id>

# 导出全部
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py --all

# 自定义输出路径
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py --output ~/backup.md

# 包含工具调用
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py --tools
```

## 输出示例

```markdown
# 对话记录

**日期:** 2026-05-01 02:13:29
**Session ID:** 20260501_021329_69e93b
**来源:** cli

---

**👤 用户:** 你好

**🤖 助手:** 你好！有什么可以帮你的？
```

## 依赖

- Python 3.8+
- `hermes` CLI 在 PATH 中

## License

MIT
