# Morning Briefing Dashboard — Claude Skill

![version](https://img.shields.io/badge/version-1.2.0-blue)

> One prompt → interactive daily kanban board, built from your real inbox, calendar, and tasks.

---

## ⬇️ Install

**[Download morning-briefing.skill →](https://github.com/Amitro1234/morning-briefing-dashboard/releases/latest/download/morning-briefing.skill)**

Then: Claude Desktop → Cowork → Plugins → **Install from file**

---

## What it does

```
start my day
```

Claude pulls from your connected sources, classifies everything by urgency, and produces a standalone HTML file you open in any browser:

| Feature | Details |
|---------|---------|
| 📋 Drag & drop | Move cards between **Todo / In Progress / Done** |
| ➕ Add tasks | `+` button in each column — title + priority tag |
| ✕ Delete | Hover any card to reveal the delete button |
| 🔗 Deep links | Cards link directly to original emails, tickets, calendar events |
| 🌐 Zero dependencies | Self-contained HTML — no server, no npm, no internet needed |
| 🌙 EOD mode | `end my day` → daily wrap-up: accomplished / carryover / tomorrow's focus |

---

## Integrations

The skill is **connector-agnostic** — it detects whatever is installed and pulls from all available sources automatically. No configuration required.

### Auto-pull (MCP connectors)

| Source type | Supported connectors | Install via |
|-------------|---------------------|-------------|
| **Email** | Outlook / Microsoft 365, Gmail / Google Workspace | Cowork → Plugins → Browse |
| **Calendar** | Outlook Calendar, Google Calendar | Cowork → Plugins → Browse |
| **Tasks & issues** | Jira, Linear, Asana, Notion, Monday, ClickUp, GitHub Issues | Cowork → Plugins → Browse |
| **Chat** | Slack, Microsoft Teams | Cowork → Plugins → Browse (used only as fallback) |

> Adding a new connector? No skill update needed — Claude detects it automatically at runtime.

### Paste-in (no connector needed)

| Source | How |
|--------|-----|
| **Jira** | Copy tickets / board view → paste in chat |
| **Obsidian** | Paste daily note — `- [ ]` / `- [/]` / `- [x]` → Todo / In Progress / Done |
| **Notion** | Paste exported content or page text |
| **GitHub / GitLab** | Paste issue list or milestone view |
| **Any text** | Free-form — Claude figures it out |

---

## Installation

### Option 1 — Cowork (Claude Desktop) ✅ Recommended

1. **[Download morning-briefing.skill](https://github.com/Amitro1234/morning-briefing-dashboard/releases/latest/download/morning-briefing.skill)**
2. Claude Desktop → Cowork → Plugins → **Install from file** → select the `.skill` file

### Option 2 — Claude Code (CLI)

```bash
# macOS / Linux
cp -r morning-briefing/ ~/.claude/skills/

# Windows (PowerShell)
Copy-Item -Recurse morning-briefing\ "$env:APPDATA\Claude\skills\"
```

### Option 3 — IDE agent (Cursor, Windsurf, etc.)

Drop this repo into your project root. The agent reads `CLAUDE.md` → follows `morning-briefing/SKILL.md` automatically.

---

## Connecting sources

**Claude Desktop → Cowork → Plugins → Browse Connectors**

Install the connectors for the tools you use. The skill works with whatever is connected — you don't need all of them. Recommended starting point:

- **Microsoft 365** — covers Outlook email + calendar + Teams in one connector
- **Jira** — pulls assigned tickets directly into the board
- **Slack** — used only as fallback when no email/calendar data is available

For paste-in sources (Jira board copy, Obsidian note, Notion export, etc.) — no connector needed, just paste directly in chat.

---

## Usage

```
start my day
morning briefing
what's on my plate today?
מה יש לי היום?
organize my tasks — here's my Jira: [paste]
end my day
set up my morning briefing every day at 7:30am
```

---

## Modes

| Mode | Trigger | Output |
|------|---------|--------|
| **Morning** | `start my day`, `morning briefing`, `מה יש לי היום` | `morning_briefing_YYYY-MM-DD.html` |
| **EOD** | `end my day`, `EOD summary`, `סיים את היום` | `eod_summary_YYYY-MM-DD.html` |

---

## File structure

```
morning-briefing-dashboard/
├── README.md                  ← you are here
├── CLAUDE.md                  ← IDE agent entry point → points to SKILL.md
├── morning-briefing.skill     ← installable skill file (Cowork / Claude Code)
└── morning-briefing/
    └── SKILL.md               ← canonical spec (single source of truth)
```

> **For contributors:** all skill logic lives exclusively in `morning-briefing/SKILL.md`.
> README and CLAUDE.md contain no duplicated implementation details.

---

## Changelog

| Version | What changed |
|---------|-------------|
| **1.2.0** | Dynamic connector detection — Jira, Linear, Asana, Monday, GitHub Issues, ClickUp auto-detected at runtime. No skill update needed when adding new connectors. |
| **1.1.0** | Generic rewrite — removed Microsoft-specific hardcoding. Works with any email/calendar/task source. Token efficiency rules added. |
| **1.0.0** | Initial release — Microsoft 365 edition. |

---

## License

MIT — free to use, share, and adapt. Built with [Claude](https://claude.ai).
