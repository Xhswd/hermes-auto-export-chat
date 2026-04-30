# hermes-auto-export-chat

导出 Hermes / Claude Code / Codex 对话记录为 Markdown

## 一句话安装

```bash
git clone https://github.com/Xhswd/hermes-auto-export-chat.git /tmp/_exp && mkdir -p ~/.hermes/skills/productivity/ && mv /tmp/_exp ~/.hermes/skills/productivity/auto-export-chat && echo done
```

## 用法

```bash
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py --list    # 列出所有会话
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py           # 导出最近对话
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py -t claude # 只导 Claude
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py -t codex  # 只导 Codex
python3 ~/.hermes/skills/productivity/auto-export-chat/scripts/export_chat.py -t hermes # 只导 Hermes
```

输出默认保存到 Windows 桌面，对话模式 (Q&A 格式)。
