# Morning Briefing Dashboard — Claude Skill (Microsoft 365 Edition)

> One prompt → interactive daily kanban board, built from your real inbox, calendar, and tasks.

---

## What it does

```
start my day
```

Claude pulls from your connected Microsoft 365 sources, classifies everything by urgency, and produces a standalone HTML file you open in any browser:

| Feature | Details |
|---------|---------|
| 📋 Drag & drop | Move cards between **Todo / In Progress / Done** |
| ➕ Add tasks | `+` button in each column — title + priority tag |
| ✕ Delete | Hover any card to reveal the delete button |
| 🔗 Deep links | Cards link directly to Outlook threads, Teams messages, Jira tickets, SharePoint docs |
| 🌐 Zero dependencies | Self-contained HTML — no server, no npm, no internet needed |
| 🌙 EOD mode | `end my day` → daily wrap-up: accomplished / carryover / tomorrow's focus |

---

## Integrations

### Auto-pull (MCP connectors)

| Source | What gets pulled |
|--------|-----------------|
| **Outlook Email** | Inbox threads, last 2 days |
| **Outlook Calendar** | Today's events + meeting prep cards |
| **Microsoft Teams** | DMs and mentions, last 24h |
| **SharePoint** | Documents updated today |

### Paste-in (no connector needed)

| Source | How |
|--------|-----|
| **Jira** | Copy tickets / board view → paste in chat — ticket IDs, status, and priority parsed automatically |
| **Obsidian** | Paste daily note — `- [ ]` / `- [/]` / `- [x]` mapped to Todo / In Progress / Done |
| **Notion** | Paste exported content or page text |
| **Any text** | Free-form — Claude figures it out |

---

## Installation

### Cowork (Claude Desktop)

1. Download `morning-briefing.skill` from [Releases](https://github.com/Amitro123/morning-briefing-dashboard/releases)
2. Claude Desktop → Cowork → **Plugins → Install from file**

### Claude Code (CLI)

```bash
# macOS / Linux
cp -r morning-briefing/ ~/.claude/skills/

# Windows
Copy-Item -Recurse morning-briefing\ "$env:APPDATA\Claude\skills\"
```

### IDE agent (Cursor, Windsurf, etc.)

Drop this repo into your project root. The agent reads `CLAUDE.md` → follows `morning-briefing/SKILL.md` automatically.

---

## Usage

```
start my day
morning briefing
what's on my plate today?
organize my tasks — here's my Jira: [paste]
end my day
set up my morning briefing every day at 7:30am
```

---

## Connecting sources

**Outlook / Teams / SharePoint / Calendar** — Cowork → Plugins → Connectors → Connect → authorize Microsoft 365

**Jira / Obsidian / Notion** — just paste in chat, no connector needed

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
├── README.md                  ← you are here (human docs)
├── CLAUDE.md                  ← IDE agent entry point → points to SKILL.md
├── morning-briefing.skill     ← installable skill file for Cowork / Claude Code
└── morning-briefing/
    └── SKILL.md               ← canonical spec (single source of truth)
```

> **For contributors:** all skill logic lives exclusively in `morning-briefing/SKILL.md`.
> README and CLAUDE.md contain no duplicated implementation details.

---

## License

MIT — free to use, share, and adapt. Built with [Claude](https://claude.ai).
