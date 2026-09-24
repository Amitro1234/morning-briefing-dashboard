# Morning Briefing — Claude Agent Entry Point

<!-- version: 1.3.2 -->

Pulled mail, calendar, and tickets are confidential. Keep titles and one-line meta only.

The canonical skill spec lives in [`morning-briefing/SKILL.md`](morning-briefing/SKILL.md).

Read it and follow it whenever the user asks for:

- a morning briefing or daily dashboard
- "start my day" / "תתחיל את היום שלי" / "מה יש לי היום"
- standup prep, daily task overview, "what's on my plate"
- organizing emails, tasks, or calendar into a visual board
- pasted content from Jira, Obsidian, Notion, Outlook, Gmail, Linear, Asana, Monday, ClickUp, GitHub, GitLab, Slack, or Teams
- an EOD summary / "end my day" / "סיים את היום שלי" / "wrap up"

**Do not duplicate the instructions here.** `SKILL.md` is the single source of truth.
The board HTML is produced only by `morning-briefing/scripts/render_board.py`.
