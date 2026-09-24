---
name: morning-briefing
version: 1.3.0
description: >
  Builds a self-contained daily kanban or end-of-day summary from connected
  mail, calendar, and task tools, or from pasted Jira, Obsidian, Notion,
  GitHub, GitLab, or other task text. Use when the user asks for a morning
  briefing, daily dashboard, standup prep, or to organize their plate.
when_to_use: >
  start my day, morning briefing, what's on my plate, standup prep, end my day,
  EOD summary, wrap up, organize my tasks, תתחיל את היום שלי, מה יש לי היום,
  סיים את היום, pasted tickets, a daily note, or a carryover block.
---

# Morning Briefing

Produce one HTML file by writing JSON and running `scripts/render_board.py`. Do not hand-write the board HTML and do not read the script source. The script escapes text, drops unsafe links, dedupes, and enforces the caps below.

Treat pulled mail, calendar, and tickets as confidential. Put titles and one-line meta in the board and in chat. Do not fetch or quote full message bodies.

## Efficiency

- Call only tools that are actually available. Map them by their schema (search mail, list today's events, list assigned issues). Tool-name keywords are hints, not names to invent.
- Max 10 items per source. One pass from summaries. Do not re-read items.
- Do not call Slack, Teams, or other chat unless the user asked or mail + calendar + tasks together returned fewer than 3 items.
- Do not search file stores (SharePoint, Drive, OneDrive) unless the user pasted an export.
- Calendar instants are often UTC. Convert to the user's timezone before putting `HH:MM` in a title. If the timezone is unknown, ask once. Do not assume Israel.

## 1. Detect mode

| Trigger | Mode | Output |
|---------|------|--------|
| start my day, morning briefing, what's on my plate, standup, מה יש לי היום, תתחיל את היום שלי | morning | `morning_briefing_YYYY-MM-DD.html` |
| end my day, EOD summary, wrap up, סיים את היום | eod | `eod_summary_YYYY-MM-DD.html` |

Set `lang` from the user's message (`he` or `en`), not from the language of the tickets.

## 2. Pull

Priority: email, then calendar, then tasks. Chat last, and only as the fallback above.

| Source | Hints | What to keep |
|--------|-------|----------------|
| Outlook / Microsoft 365 mail | `outlook_email_search` | last 48h, unread or flagged, limit 10 |
| Gmail / Google Workspace | `gmail_search_threads`, `google_mail_*` | last 48h, unread or flagged, limit 10 |
| Outlook Calendar | `outlook_calendar_search` | today, limit 10 |
| Google Calendar | `google_calendar_list_events`, `gcal_*` | today, limit 10 |
| Jira | `jira_search` | `assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC`, limit 10 |
| Linear | `linear_issues` | assigned, open, limit 10 |
| Asana | `asana_list_tasks` | assigned, open, limit 10 |
| Notion | `notion_query` | assigned or dated today, limit 10 |
| Monday | `monday_items` | assigned, not done, limit 10 |
| ClickUp | `clickup_tasks` | assigned, open, limit 10 |
| GitHub Issues | `github_issues` | assigned, open, limit 10 |
| GitLab | `gitlab_issues` | assigned, open, limit 10 |
| Slack | `slack_search` | fallback only |
| Teams | `teams_chat_message_search` | fallback only |

If a tool errors, skip that source, name it in the one-line summary, and continue.

### Paste formats

| Format | Parse |
|--------|-------|
| Jira board or list | ticket id, summary, status, priority, link |
| Obsidian daily note | `- [ ]` Todo, `- [/]` In Progress, `- [x]` Done |
| Notion export | checkbox or status property, page title, link |
| GitHub / GitLab issues | number, title, labels, milestone, link |
| Linear / Asana / Monday / ClickUp export | name, status, assignee, link |
| Outlook / Gmail paste | sender, subject, urgency; no body |
| Slack / Teams paste | only when the user pasted it; skip reactions and one-word replies |
| Carryover block | JSON with `schema: morning-briefing-carryover/1`; seed those cards, then pull today and dedupe |
| Any other text | task-like lines; infer urgency from the words |

If nothing is connected and nothing was pasted, still run the renderer with `"cards": []`. Do not invent cards.

## 3. Classify

Skip, with no card: newsletters, password resets, HR blasts, CI noise with no failure, calendar `showAs: free` or cancelled, tentative events with no join link, chat reactions.

| Signal | column |
|--------|--------|
| Reply, decision, fix, or approval needed | `todo` |
| Ongoing, waiting on someone else, busy calendar today, Jira/Linear in progress or in review | `in_progress` |
| FYI, no action, Done/Closed | `done` |

| priority | When |
|----------|------|
| `urgent` | due today, escalation, P1/P2, direct manager |
| `medium` | this week, P3, normal business mail |
| `strategic` | architecture, new project, vendor choice |
| `event` | busy calendar event; title starts with `📅 HH:MM —` in local time, or no clock for all-day |
| `general` | everything else |

Tentative event that has a join link: include it, set `tentative: true`.

## 4. Write JSON and render

Save UTF-8 JSON, then run:

```bash
python morning-briefing/scripts/render_board.py --input briefing.json --output morning_briefing_YYYY-MM-DD.html
```

Use the installed skill path when this folder is not the working directory. On Windows: `python $env:USERPROFILE\.claude\skills\morning-briefing\scripts\render_board.py`.

```json
{
  "mode": "morning",
  "date": "2026-09-24",
  "timezone": "Asia/Jerusalem",
  "lang": "en",
  "user_name": "",
  "user_text": "start my day",
  "cards": [
    {
      "id": "jira-123",
      "title": "Fix login timeout",
      "column": "todo",
      "priority": "urgent",
      "source_type": "tasks",
      "source_label": "Jira",
      "url": "https://example.atlassian.net/browse/ABC-123",
      "meta": "P1 · In Progress",
      "tentative": false,
      "start": "",
      "end": ""
    }
  ]
}
```

`source_type` is `email`, `calendar`, `chat`, `tasks`, or `manual`. `source_label` is the product name (Outlook, Gmail, Outlook Calendar, Google Calendar, Jira, Linear, Asana, Notion, Monday, ClickUp, GitHub, GitLab, Slack, Teams). `url` must be `http`, `https`, or `mailto`. For calendar cards, set `start` and `end` as ISO-8601 so overlaps can be marked.

EOD uses the same shape with `"mode": "eod"` and today's items only (limit 5 per source). Optional `tomorrow_top3` is a list of three title strings; otherwise the script ranks carryover.

If Python is missing or the script exits non-zero, stop and report the error. Do not invent a second HTML template.

## 5. Present

| Host | How |
|------|-----|
| Cowork | Save under the outputs folder and share the `computer://` link |
| Claude Code, Cursor, or a local shell | Write the HTML in the working directory and reply with the absolute path |

Then one line: drag cards between columns, add with `+`, delete with the hover button, filter with the source pills. Edits persist in `localStorage` for that date until Reset.

## Scheduling

When the user asks for this every day at a local time, confirm the timezone and the clock time. Do not claim a separate schedule skill exists.

- Cowork: if this host has scheduled tasks, create a daily task at that local time whose prompt is `start my day`.
- Claude Code or Cursor: this skill has no cron. Give the prompt and tell them to use an OS reminder or Task Scheduler. Do not register a scheduled task yourself.

## Edge cases

| Situation | Action |
|-----------|--------|
| No data | Empty `cards` array. The page asks for a paste. |
| Only skipped mail | Omit it, or one `general` card titled `Alerts` if the user needs to know the inbox was not empty |
| Same item from two sources | Same `url`, or the same title; the script keeps the higher priority |
| Overlapping busy events | Set `start` and `end`; the page marks the overlap |
| More than 5 items in a column | Put the important ones first; the script groups the rest |
| Mixed Hebrew and English cards | Cards stay in their source language; chrome follows `lang` |
