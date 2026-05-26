# Morning Briefing Dashboard — Claude Skill

![version](https://img.shields.io/badge/version-1.1.0-blue)

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

### Auto-pull (MCP connectors)

Works with any connected source — the skill detects what's available and pulls accordingly:

| Source type | Examples |
|-------------|---------|
| **Email** | Outlook, Gmail |
| **Calendar** | Outlook Calendar, Google Calendar |
| **Tasks & issues** | Jira, Linear, Asana, Notion |
| **Chat** | Teams, Slack — used only if no other data available |

### Paste-in (no connector needed)

| Source | How |
|--------|-----|
| **Jira** | Copy tickets / board view → paste in chat |
| **Obsidian** | Paste daily note — `- [ ]` / `- [/]` / `- [x]` → Todo / In Progress / Done |
| **Notion** | Paste exported content or page text |
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

Connect any source via Cowork → Plugins → Connectors. The skill works with whatever is connected — no need for all of them.

For paste-in sources (Jira, Obsidian, Notion, etc.) — just paste content directly in chat, no connector needed.

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

## License

MIT — free to use, share, and adapt. Built with [Claude](https://claude.ai).
