---
name: morning-briefing
description: >
  Generates a daily morning briefing as an interactive HTML kanban board (Todo / In Progress / Done).
  Auto-pulls from connected Microsoft 365 sources — Outlook email, Outlook Calendar, Microsoft Teams,
  SharePoint — and also accepts pasted content from Jira, Obsidian, Notion, or any free text.
  Use this skill whenever the user asks for a morning briefing, daily dashboard, "what's on my plate today",
  standup prep, daily task overview, or wants to organize their emails and tasks into a visual board.
  Also triggers for "start my day", "תתחיל את היום שלי", "מה יש לי היום", "organize my tasks",
  "what should I focus on today", "kanban from my emails", or when the user pastes a block of tasks/emails.
  Also handles EOD / end-of-day mode when user says "end my day", "סיים את היום שלי", "EOD summary".
---

# Morning Briefing — Daily Kanban Dashboard

Produces a self-contained HTML file: `morning_briefing_YYYY-MM-DD.html`
Features: drag-and-drop kanban (Todo / In Progress / Done), AI priority scoring, meeting prep cards,
cards from live Microsoft 365 sources or pasted text, `+` button per column for manual tasks,
`✕` delete on hover, deep links to source items.

Supports two modes — detect from user intent:
- **Morning mode** (default): full board build from all sources
- **EOD mode**: triggered by "end my day" / "EOD summary" — shows what's done, what's open, what moves to tomorrow

---

## Step 1 — Detect mode

| User says | Mode |
|-----------|------|
| "start my day", "morning briefing", "מה יש לי היום" | **Morning** |
| "end my day", "EOD", "סיים את היום", "wrap up" | **EOD** |

If EOD → skip to [EOD Section](#eod-mode) at the bottom.

---

## Step 2 — Gather data (Morning mode)

Pull from all available sources **in parallel**.

### MCP connectors (auto-pull if tools are available)

| Source | Tool | Query |
|--------|------|-------|
| Outlook Email | `outlook_email_search` | last 2 days, inbox, unread/flagged first — up to 20 items |
| Outlook Calendar | `outlook_calendar_search` | today full day, user timezone |
| Microsoft Teams | `chat_message_search` | last 24h, mentions of user or direct messages — up to 15 items |
| SharePoint | `sharepoint_search` | documents modified today relevant to user — up to 10 items |

> If a connector returns an error, skip it silently and continue with what's available.

### Pasted input (no connector needed)

Accept any pasted content alongside or instead of MCP data:

| Format | Signals to extract |
|--------|--------------------|
| Jira board / ticket list | Ticket ID (e.g. `PROJ-123`), status, assignee, priority label |
| Jira export (CSV/text) | Parse columns: Summary, Status, Priority, Assignee |
| Obsidian daily note | `- [ ]` → Todo, `- [x]` → Done, `- [/]` → In Progress, headings as context |
| Notion export / paste | Checkbox items, status properties, page titles |
| Outlook email subjects | Sender, subject, urgency keywords (`FWD:`, `RE:`, `URGENT`, deadline dates) |
| Free text / any list | Extract task-like items; infer urgency from language |

If nothing is available and nothing is pasted, ask:
> "רוצה להדביק אימיילים, Jira tickets, או רשימת tasks? אני אסדר הכל."

---

## Step 3 — Classify and score items

### Column mapping

| Signal | Column |
|--------|--------|
| Requires reply, fix, decision, or approval | **Todo** |
| Ongoing, pending someone else, event to prepare for, Jira "In Review" / "In Progress" | **In Progress** |
| Confirmations, FYI, read-only notifications, Jira "Done" / "Closed" | **Done** (0.6 opacity) |
| Newsletters, automated alerts with no action needed | One grouped card, or skip |

Don't create a card for every item — use judgment. Max ~5 cards per column; group low-priority items.
Jira items in "Waiting for Review" status where the user is the reporter → **In Progress**.

### AI Priority scoring

For each card, infer priority from content, sender, and context:

| Badge | When |
|-------|------|
| 🔴 Urgent | Deadline today, CI failure, escalation, manager/CIO in sender, Jira P1/P2 |
| 🟡 Medium | Action needed this week, Jira P3, Teams mention without urgency |
| 🔵 Strategic | AI initiative, architecture decision, stakeholder sync, new project scoping |
| 🟢 Event | Calendar item, confirmed meeting — include time in card title |
| ⚪ General | Everything else |

**Meeting prep cards** — for each calendar event today:
- If event has >1 attendee → create a card in **In Progress** column
- Card title: `📅 HH:MM — [Meeting title]`
- Card body: attendees count, location/Teams link if available
- Priority: 🟢 Event (or 🔴 Urgent if it's in <30 min)

---

## Step 4 — Build the HTML file

Single self-contained file, no external dependencies.

### Layout

Three columns (CSS grid): 📋 Todo / 🔄 In Progress / ✅ Done
Each column: header + live count badge + card list + `+` add button

Header bar (top of page):
- Left: date (`יום ראשון, 1 בינואר 2026` style — Hebrew if RTL, English otherwise; always use today's actual date)
- Right: source pills showing which connectors contributed data (e.g. `📧 Outlook` `📅 Calendar` `💬 Teams`)
- Center: greeting — "בוקר טוב ☀️" (Hebrew) or "Good morning ☀️" (English)

### Card structure

```
┌────────────────────────────────────────┐
│ ⠿  [× on hover]                        │
│    Title (concise, ~50 chars max)      │
│    [Source badge] [Priority badge]     │
│    Link to original ↗ (if available)  │
└────────────────────────────────────────┘
```

### Add task form

`+` → inline form per column:
- Text input + tag selector (None / 🔴 Urgent / 🟡 Medium / 🔵 Strategic / 🟢 Event / ⚪ General)
- Enter confirms, Escape cancels, count updates on add

### Drag and drop — mouse events only (not HTML5 drag API)

```
mousedown → clone card as floating ghost (fixed pos), add .ghost to original
mousemove → move ghost with cursor, show 3px blue drop indicator between cards
mouseup   → insert original at indicator, remove ghost, update counts
```

Done-column drops: set card `opacity: 0.6`.

### Design tokens

```css
body:        background #f5f5f3
column:      background #ebebea, border-radius 12px
card:        background #fff, border 0.5px solid #e0e0dc, border-radius 10px
font:        -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif

/* Priority badges */
.badge-red      { background: #FCEBEB; color: #a32d2d; }
.badge-amber    { background: #FAEEDA; color: #854f0b; }
.badge-blue     { background: #E6F1FB; color: #185fa5; }
.badge-green    { background: #EAF3DE; color: #3b6d11; }
.badge-gray     { background: #f1efe8; color: #666;    }

/* Source badges */
Outlook Email    → blue      (#E6F1FB / #185fa5)
Outlook Calendar → green     (#EAF3DE / #3b6d11)
Teams            → purple    (#EEEDFE / #534AB7)
SharePoint       → teal      (#E0F4F4 / #0f7b7b)
Jira             → blue-dark (#dbe9ff / #0052CC)
Obsidian         → purple    (#EEEDFE / #534AB7)
Notion           → dark      (#e8e8e4 / #37352f)
Manual           → gray      (#f1efe8 / #666)
```

RTL support: `<html dir="rtl">` when content is primarily Hebrew.
Mixed Hebrew/English cards: cards stay in original language; layout is bilingual-friendly.

---

## Step 5 — Save and present

1. Save as `morning_briefing_YYYY-MM-DD.html` in the outputs folder
2. Provide a `computer://` link
3. Add one line: "גרור כרטיסים בין עמודות, הוסף tasks עם `+`, מחק עם hover ו-`✕`."
   (or English equivalent if user wrote in English)
4. Offer: "רוצה שארוץ את זה אוטומטית כל בוקר? אפשר לתזמן עם ה-schedule skill."

---

## EOD Mode

Triggered by: "end my day", "EOD", "סיים את היום", "daily wrap-up"

### EOD data pull

Same MCP sources as morning, but filter for **today only**:
- Outlook: emails sent today by user + emails received and replied to
- Teams: messages sent today by user
- Calendar: events that already ended today

### EOD HTML output

File: `eod_summary_YYYY-MM-DD.html`

Three sections (read-only, no drag-and-drop):

| Section | Content |
|---------|---------|
| ✅ Accomplished today | Items moved to Done + sent emails + completed Jira tickets |
| 🔄 Carrying over | Items still in Todo/In Progress → auto-moved to tomorrow's board |
| 📋 Tomorrow's focus | Top 3 priorities for tomorrow (AI-scored from carryover) |

Footer: "סיכום יום — [date]" with time of generation.

After presenting EOD file, ask:
> "רוצה שאשלח את הסיכום ב-Teams לצוות שלך?"

---

## Edge cases

| Situation | Handling |
|-----------|---------|
| No connectors, nothing pasted | Ask user to paste or connect. Don't generate empty board. |
| Only newsletters/automated alerts | Group into one "Alerts (skip)" card in Todo |
| 20+ items | Max ~5 per column, group low-priority under one "וכו'..." card |
| Mixed Hebrew/English | Cards stay in original language; UI adapts to dominant language |
| Jira items with no assignee | Skip (not the user's problem) |
| SharePoint docs — no clear action | One grouped card: "📄 Updated docs today (N)" |
| User wants automation | Suggest `schedule` skill for daily runs at a set time |
| Teams message is just a reaction/emoji | Skip |
