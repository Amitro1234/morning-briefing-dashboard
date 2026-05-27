---
name: morning-briefing
version: 1.2.0
description: >
  Generates a daily morning briefing as an interactive HTML kanban board (Todo / In Progress / Done).
  Works with ANY connected source — Outlook, Gmail, Google Calendar, Jira, Notion, Obsidian, Slack,
  Teams, Linear, Asana, or plain pasted text. Use when the user asks for a morning briefing,
  daily dashboard, "start my day", "תתחיל את היום שלי", "מה יש לי היום", "what's on my plate",
  standup prep, or pastes tasks/emails to organize. Also handles EOD mode: "end my day", "סיים את היום".
---

# Morning Briefing — Daily Kanban Dashboard

Produces: `morning_briefing_YYYY-MM-DD.html` — self-contained, no dependencies.

---

## IMPORTANT: efficiency rules

- **Token budget is precious.** Pull the minimum needed. Do NOT fetch full email bodies.
- **Max items per source: 10.** Stop there even if more exist.
- **Call only sources that are actually connected.** Check tool availability before calling.
- **Do not call Teams/Slack/SharePoint by default** — only if the user asks or no other source has data.
- **One pass.** Classify directly from search result summaries. Do not re-read items.
- **Timezone:** Calendar tools return UTC. Always convert to the user's local time before displaying. If unknown, ask once. Israel = UTC+3 (IDT, summer).

---

## Step 1 — Detect mode

| Trigger | Mode |
|---------|------|
| "start my day", "morning briefing", "מה יש לי" | **Morning** (default) |
| "end my day", "EOD", "סיים את היום" | **EOD** → skip to EOD section |

---

## Step 2 — Discover and pull data

### 2a. Connector detection — dynamic source discovery

Before pulling anything, scan available tools and build a source map. Pull **only** from connected sources. The skill adapts automatically to whatever is installed — do not hardcode assumptions.

**Priority order:**

| Priority | Source type | Example tools | Query / filter |
|----------|-------------|---------------|----------------|
| 1 | **Email** | `outlook_email_search`, `gmail_search_threads`, `google_mail_*` | Last 48h, unread or flagged, **limit 10** |
| 2 | **Calendar** | `outlook_calendar_search`, `google_calendar_list_events`, `gcal_*` | Today only, **limit 10** |
| 3 | **Tasks / issues** | `jira_search`, `jira_get_issues`, `linear_issues`, `asana_list_tasks`, `notion_query`, `monday_items`, `clickup_tasks`, `github_issues`, `gitlab_issues` | Assigned to user, open/in-progress, **limit 10** |
| 4 | **Chat** (optional) | `slack_search`, `slack_search_public`, `teams_chat_message_search`, `discord_search` | Only if priorities 1–3 return < 3 items total |

> **New connector installed?** No skill update needed. As long as the tool name contains recognizable keywords (`jira`, `linear`, `asana`, `notion`, `gmail`, `calendar`, `slack`, etc.), Claude will detect and pull from it automatically.

**Jira-specific query hints** (when Jira connector is available):
- Filter: `assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC`
- Include: ticket ID, summary, status, priority, sprint
- Source badge: 🔵 Tasks (amber)

### 2b. Pasted input

If the user pastes content alongside or instead of connected data, parse it:

| Format | How to parse |
|--------|-------------|
| Jira board/list | Extract: ticket ID, summary, status, priority |
| Obsidian daily note | `- [ ]` → Todo · `- [/]` → In Progress · `- [x]` → Done |
| Notion paste | Checkbox items and status properties |
| Outlook/Gmail email text | Sender, subject, urgency signals |
| Linear / Asana / Monday export | Task name, status, assignee |
| GitHub / GitLab issues | Issue number, title, labels, milestone |
| Any free text | Extract task-like items; infer urgency from language |

### 2c. Nothing available

If no tools are connected and nothing is pasted:
> "רוצה להדביק תוכן? Jira tickets, אימיילים, Obsidian note — אני אסדר הכל."

Do NOT generate a board with invented data.

---

## Step 3 — Classify (one pass, directly from summaries)

### What to skip entirely (no card)

- Automated system emails (monitoring alerts, CI notifications with no failure, password resets, newsletters, ratings reports, HR announcements)
- Calendar events marked `showAs: free` or `isCancelled: true`
- Calendar events marked `tentative` — include only if they have an explicit Zoom/Teams link (mark with ⚠️ tentative)
- Chat messages that are pure reactions, short replies ("כן", "אני שומע", links only)

### Column mapping

| Signal | Column |
|--------|--------|
| Requires a reply, decision, fix, or approval from the user | **Todo** |
| Ongoing work, waiting on someone else, confirmed calendar event today, Jira "In Progress" / "In Review" | **In Progress** |
| FYI only, read and no action needed, Jira "Done" / "Closed", confirmed/received | **Done** |

**Max 5 cards per column.** If more items qualify, group the lowest-priority ones into a single "וכו'..." card.

### Priority badges

| Badge | When |
|-------|------|
| 🔴 Urgent | Deadline today, explicit escalation, Jira P1/P2, direct manager |
| 🟡 Medium | Action needed this week, Jira P3, normal business email |
| 🔵 Strategic | Architecture decision, AI initiative, new project, vendor evaluation |
| 🟢 Event | Confirmed calendar event — prepend `📅 HH:MM —` to title (local time) |
| ⚪ General | Everything else |

### Meeting cards (calendar events)

- Only include events with `showAs: busy` (not free, not tentative unless has a join link)
- Include attendee count and location/link in card meta
- Format: `📅 HH:MM — [title]` where HH:MM is **local time** (converted from UTC)

---

## Step 4 — Build HTML

Single self-contained file. No external dependencies. RTL (`dir="rtl"`) when content is primarily Hebrew.

### Structure

```
Header bar:
  left: date in local language (יום X, DD בחודש YYYY)
  center: greeting ☀️ (use user's name if known)
  right: source pills — one per connected source that contributed data

Three columns (CSS grid): 📋 Todo / 🔄 In Progress / ✅ Done
Each column: title + live count + card list + [+] add button
```

### Card structure

```
┌──────────────────────────────────┐
│ ⠿                            [×] │  ← drag handle + delete on hover
│ Title (~50 chars max)            │
│ [Source badge] [Priority badge]  │
│ Link to original ↗ (if exists)  │
│ Meta line (attendees, time, etc) │
└──────────────────────────────────┘
```

### Add task form

`+` opens inline form per column: text input + priority tag picker (Enter = confirm, Escape = cancel).

### Drag & drop — mouse events only (NOT HTML5 drag API)

```
mousedown → clone as ghost (fixed position), mark original as dragging
mousemove → move ghost, show 3px blue drop indicator between cards
mouseup   → insert card at indicator, remove ghost, update column counts
```

Done column: set dropped card to `opacity: 0.6`.

### Design tokens

```css
body:           background #f5f5f3
column:         background #ebebea, border-radius 12px
card:           background #fff, border 0.5px solid #e0e0dc, border-radius 10px
font:           -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif

/* Priority badges */
.b-red    { background:#FCEBEB; color:#a32d2d }
.b-amber  { background:#FAEEDA; color:#854f0b }
.b-blue   { background:#E6F1FB; color:#185fa5 }
.b-green  { background:#EAF3DE; color:#3b6d11 }
.b-gray   { background:#f1efe8; color:#5F5E5A }

/* Source badges — assign by source type, not by specific tool */
Email     → blue   (#E6F1FB / #185fa5)
Calendar  → green  (#EAF3DE / #3b6d11)
Chat      → purple (#EEEDFE / #534AB7)
Tasks     → amber  (#FAEEDA / #854f0b)   /* Jira, Linear, Asana, Notion */
Manual    → gray   (#f1efe8 / #5F5E5A)
```

---

## Step 5 — Save and present

1. Save as `morning_briefing_YYYY-MM-DD.html` in outputs folder
2. Share a `computer://` link
3. One line: "גרור כרטיסים בין עמודות · הוסף עם `+` · מחק עם ✕ בריחוף"
4. Optionally offer: "רוצה לקבל את זה אוטומטית כל בוקר? אפשר לתזמן."

---

## EOD Mode

Triggered by: "end my day" / "EOD" / "סיים את היום"

**Data pull:** Same sources, filter for today only. Limit 5 per source.

**Output file:** `eod_summary_YYYY-MM-DD.html` — read-only, three sections:

| Section | Content |
|---------|---------|
| ✅ Accomplished | Emails sent/replied, Jira items closed, events completed |
| 🔄 Carrying over | Open Todo items → will become tomorrow's board |
| 📋 Tomorrow's top 3 | AI-ranked priorities from carryover |

---

## Edge cases

| Situation | Action |
|-----------|--------|
| No data anywhere | Ask user to paste. Never invent cards. |
| Only newsletters/automated | One grouped "Alerts (skip)" card, or omit entirely |
| >15 total items | Cap at 5 per column, group remainder |
| Tentative event, no join link | Skip |
| Tentative event + join link | Include, mark ⚠️ לא אושר |
| UTC times from calendar | Always convert to local time before showing |
| Mixed Hebrew/English | Cards stay in source language; UI adapts to majority |
| User wants scheduling | Suggest `schedule` skill |
