#!/usr/bin/env python3
"""Render a morning-briefing or end-of-day HTML file from a JSON payload.

Run this script. Do not hand-write the board HTML.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from urllib.parse import urlsplit

MAX_PER_SOURCE = 10
MAX_PER_COLUMN = 5
PRIORITIES = ("urgent", "medium", "strategic", "event", "general")
COLUMNS = ("todo", "in_progress", "done")
SOURCE_TYPES = ("email", "calendar", "chat", "tasks", "manual")
PRIORITY_RANK = {name: index for index, name in enumerate(PRIORITIES)}

STRINGS = {
    "en": {
        "todo": "Todo",
        "in_progress": "In Progress",
        "done": "Done",
        "focus": "Top 3 focus",
        "empty": "Nothing to pull yet. Paste Jira, email, an Obsidian note, Notion, GitHub, GitLab, or any task list.",
        "add": "Add",
        "delete": "Delete",
        "reset": "Reset to generated",
        "open": "Open",
        "more": "+{n} more",
        "overlap": "Overlaps",
        "tentative": "Tentative",
        "accomplished": "Accomplished",
        "carryover": "Carrying over",
        "tomorrow": "Tomorrow's top 3",
        "carryover_help": "Paste this block into tomorrow's morning briefing to seed the board.",
        "sources": "Sources",
        "filter_all": "All",
        "greeting": "Good morning",
        "eod_title": "End of day",
        "no_script": "This board needs JavaScript for drag, add, and delete. Items are listed below.",
    },
    "he": {
        "todo": "לעשות",
        "in_progress": "בתהליך",
        "done": "הושלם",
        "focus": "3 המיקוד להיום",
        "empty": "אין עדיין נתונים. אפשר להדביק Jira, אימייל, פתק Obsidian, Notion, GitHub, GitLab, או כל רשימת משימות.",
        "add": "הוספה",
        "delete": "מחיקה",
        "reset": "חזרה ללוח שנוצר",
        "open": "פתיחה",
        "more": "ועוד {n}",
        "overlap": "חפיפה",
        "tentative": "לא אושר",
        "accomplished": "הושלם היום",
        "carryover": "עובר למחר",
        "tomorrow": "3 העדיפויות למחר",
        "carryover_help": "הדביקו את הבלוק הזה בבוקר כדי לזרוע את הלוח.",
        "sources": "מקורות",
        "filter_all": "הכל",
        "greeting": "בוקר טוב",
        "eod_title": "סיכום יום",
        "no_script": "הלוח צריך JavaScript לגרירה, הוספה ומחיקה. הפריטים מופיעים למטה.",
    },
}


def safe_url(url: object) -> str:
    if not isinstance(url, str):
        return ""
    candidate = url.strip()
    if not candidate or any(ord(ch) < 32 for ch in candidate):
        return ""
    parts = urlsplit(candidate)
    if parts.scheme.lower() in {"http", "https", "mailto"}:
        return candidate
    return ""


def _clean_text(value: object, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text[:limit]


def _hebrew_count(text: str) -> int:
    return len(re.findall(r"[\u0590-\u05FF]", text))


def choose_lang(payload: dict, cards: list[dict]) -> str:
    requested = payload.get("lang")
    if requested in {"he", "en"}:
        return requested
    blob = " ".join(card.get("title", "") for card in cards)
    user_text = payload.get("user_text") if isinstance(payload.get("user_text"), str) else ""
    blob = f"{user_text} {blob}"
    return "he" if _hebrew_count(blob) > len(re.findall(r"[A-Za-z]", blob)) else "en"


def _parse_instant(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _normalize_card(raw: object, index: int) -> dict | None:
    if not isinstance(raw, dict):
        return None
    title = _clean_text(raw.get("title"), 180)
    if not title:
        return None
    column = raw.get("column") if raw.get("column") in COLUMNS else "todo"
    priority = raw.get("priority") if raw.get("priority") in PRIORITIES else "general"
    source_type = raw.get("source_type") if raw.get("source_type") in SOURCE_TYPES else "manual"
    card_id = _clean_text(raw.get("id"), 80) or f"card-{index}"
    return {
        "id": card_id,
        "title": title,
        "column": column,
        "priority": priority,
        "source_type": source_type,
        "source_label": _clean_text(raw.get("source_label"), 40),
        "url": safe_url(raw.get("url")),
        "meta": _clean_text(raw.get("meta"), 180),
        "tentative": bool(raw.get("tentative")),
        "start": raw.get("start") if _parse_instant(raw.get("start")) else "",
        "end": raw.get("end") if _parse_instant(raw.get("end")) else "",
        "overlap_with": "",
    }


def _dedupe(cards: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    order: list[str] = []
    for card in cards:
        key = card["url"] or re.sub(r"\W+", " ", card["title"].casefold()).strip()
        previous = seen.get(key)
        if previous is None:
            seen[key] = card
            order.append(key)
            continue
        if PRIORITY_RANK[card["priority"]] < PRIORITY_RANK[previous["priority"]]:
            seen[key] = card
    return [seen[key] for key in order]


def _cap_sources(cards: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    kept: list[dict] = []
    ranked = sorted(cards, key=lambda card: PRIORITY_RANK[card["priority"]])
    for card in ranked:
        label = card["source_label"] or card["source_type"]
        counts[label] = counts.get(label, 0) + 1
        if counts[label] <= MAX_PER_SOURCE:
            kept.append(card)
    kept_ids = {card["id"] for card in kept}
    return [card for card in cards if card["id"] in kept_ids]


def _mark_overlaps(cards: list[dict]) -> None:
    calendar = [card for card in cards if card["source_type"] == "calendar" and card["start"] and card["end"]]
    for left in calendar:
        left_start = _parse_instant(left["start"])
        left_end = _parse_instant(left["end"])
        if left_start is None or left_end is None:
            continue
        overlaps = []
        for right in calendar:
            if right is left:
                continue
            right_start = _parse_instant(right["start"])
            right_end = _parse_instant(right["end"])
            if right_start is None or right_end is None:
                continue
            if left_start < right_end and right_start < left_end:
                overlaps.append(right["title"])
        if overlaps:
            left["overlap_with"] = overlaps[0]


def _cap_columns(cards: list[dict], lang: str) -> list[dict]:
    grouped: list[dict] = []
    for column in COLUMNS:
        members = [card for card in cards if card["column"] == column]
        members.sort(key=lambda card: PRIORITY_RANK[card["priority"]])
        if len(members) <= MAX_PER_COLUMN:
            grouped.extend(members)
            continue
        grouped.extend(members[:MAX_PER_COLUMN])
        extra = members[MAX_PER_COLUMN:]
        preview = "; ".join(card["title"] for card in extra[:8])
        grouped.append(
            {
                "id": f"grouped-{column}",
                "title": STRINGS[lang]["more"].format(n=len(extra)),
                "column": column,
                "priority": "general",
                "source_type": "manual",
                "source_label": "",
                "url": "",
                "meta": preview,
                "tentative": False,
                "start": "",
                "end": "",
                "overlap_with": "",
            }
        )
    return grouped


def _focus(cards: list[dict]) -> list[str]:
    pool = [card for card in cards if card["column"] == "todo" and not card["id"].startswith("grouped-")]
    pool.sort(key=lambda card: PRIORITY_RANK[card["priority"]])
    return [card["title"] for card in pool[:3]]


def _eod(cards: list[dict], payload: dict) -> dict:
    accomplished = [card["title"] for card in cards if card["column"] == "done"]
    carryover_cards = [card for card in cards if card["column"] in {"todo", "in_progress"} and not card["id"].startswith("grouped-")]
    explicit = payload.get("tomorrow_top3")
    if isinstance(explicit, list) and explicit:
        tomorrow = [_clean_text(item, 180) for item in explicit if _clean_text(item, 180)][:3]
    else:
        ranked = sorted(carryover_cards, key=lambda card: (0 if card["column"] == "todo" else 1, PRIORITY_RANK[card["priority"]]))
        tomorrow = [card["title"] for card in ranked[:3]]
    return {
        "accomplished": accomplished,
        "carryover": [
            {"title": card["title"], "column": card["column"], "priority": card["priority"], "source_label": card["source_label"]}
            for card in carryover_cards
        ],
        "tomorrow_top3": tomorrow,
    }


def prepare(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    mode = payload.get("mode") if payload.get("mode") in {"morning", "eod"} else "morning"
    date = payload.get("date") if isinstance(payload.get("date"), str) else ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date or ""):
        date = datetime.now().strftime("%Y-%m-%d")
    raw_cards = payload.get("cards") if isinstance(payload.get("cards"), list) else []
    cards = [card for index, raw in enumerate(raw_cards) if (card := _normalize_card(raw, index))]
    lang = choose_lang(payload, cards)
    cards = _dedupe(cards)
    cards = _cap_sources(cards)
    _mark_overlaps(cards)
    cards = _cap_columns(cards, lang)
    sources = []
    for card in cards:
        label = card["source_label"]
        if label and label not in sources:
            sources.append(label)
    user_name = _clean_text(payload.get("user_name"), 60)
    return {
        "schema": "morning-briefing/1",
        "mode": mode,
        "date": date,
        "timezone": _clean_text(payload.get("timezone"), 64) or "local",
        "lang": lang,
        "user_name": user_name,
        "sources": sources,
        "focus": _focus(cards),
        "cards": cards,
        "eod": _eod(cards, payload),
        "strings": STRINGS[lang],
    }


def _json_for_script(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render(payload: object) -> str:
    board = prepare(payload)
    lang = board["lang"]
    direction = "rtl" if lang == "he" else "ltr"
    strings = board["strings"]
    title = strings["eod_title"] if board["mode"] == "eod" else strings["greeting"]
    embedded = _json_for_script(board)
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} {board["date"]}</title>
<style>
:root {{ color-scheme: light; }}
body {{ margin: 0; background: #f5f5f3; color: #1f1e1b; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
header, main {{ padding: 16px 20px; }}
header {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; }}
h1 {{ font-size: 1.25rem; margin: 0; }}
.pills, .focus, .columns, .eod {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.pill, button {{ border: 0; border-radius: 999px; padding: 4px 10px; background: #fff; cursor: pointer; }}
.pill[aria-pressed="true"] {{ outline: 2px solid #185fa5; }}
.focus {{ margin-top: 8px; }}
.columns {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; align-items: start; }}
.column {{ background: #ebebea; border-radius: 12px; padding: 10px; min-height: 180px; }}
.column h2 {{ margin: 0 0 8px; font-size: 1rem; }}
.card {{ background: #fff; border: 0.5px solid #e0e0dc; border-radius: 10px; padding: 10px; margin: 0 0 8px; position: relative; }}
.card.done {{ opacity: 0.6; }}
.card.over {{ outline: 3px solid #185fa5; }}
.handle {{ cursor: grab; color: #5F5E5A; }}
.badges {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }}
.badge {{ border-radius: 999px; padding: 2px 8px; font-size: 12px; }}
.b-red {{ background: #FCEBEB; color: #a32d2d; }}
.b-amber {{ background: #FAEEDA; color: #854f0b; }}
.b-blue {{ background: #E6F1FB; color: #185fa5; }}
.b-green {{ background: #EAF3DE; color: #3b6d11; }}
.b-purple {{ background: #EEEDFE; color: #534AB7; }}
.b-gray {{ background: #f1efe8; color: #5F5E5A; }}
.delete, .reset {{ float: inline-end; }}
.card .delete {{ opacity: 0; }}
.card:hover .delete, .card:focus-within .delete {{ opacity: 1; }}
.add-form {{ display: flex; gap: 6px; flex-wrap: wrap; }}
.add-form input, .add-form select {{ border-radius: 8px; border: 1px solid #e0e0dc; padding: 6px; }}
.section {{ background: #fff; border-radius: 12px; padding: 12px; margin: 0 0 12px; }}
textarea {{ width: 100%; min-height: 8rem; }}
.ghost {{ position: fixed; pointer-events: none; opacity: 0.85; z-index: 5; }}
@media (max-width: 800px) {{ .columns {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <div>
    <h1 id="title"></h1>
    <div class="pills" id="pills"></div>
    <div class="focus" id="focus"></div>
  </div>
  <button type="button" class="reset" id="reset"></button>
</header>
<main id="app"></main>
<noscript><p>{strings["no_script"]}</p></noscript>
<script type="application/json" id="board-data">{embedded}</script>
<script>
const board = JSON.parse(document.getElementById("board-data").textContent);
const strings = board.strings;
const storageKey = "morning-briefing:" + board.date + ":" + board.mode;
const priorityClass = {{ urgent: "b-red", medium: "b-amber", strategic: "b-blue", event: "b-green", general: "b-gray" }};
const sourceClass = {{ email: "b-blue", calendar: "b-green", chat: "b-purple", tasks: "b-amber", manual: "b-gray" }};
const columnOrder = ["todo", "in_progress", "done"];
let filter = "all";
let drag = null;

function loadState() {{
  try {{
    const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
    if (saved && Array.isArray(saved.cards)) return saved.cards;
  }} catch (err) {{}}
  return board.cards;
}}
let cards = loadState();

function persist() {{
  localStorage.setItem(storageKey, JSON.stringify({{ cards }}));
}}

function el(tag, text, className) {{
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}}

function safeHref(url) {{
  try {{
    const parsed = new URL(url, "https://example.invalid");
    if (parsed.protocol === "http:" || parsed.protocol === "https:" || parsed.protocol === "mailto:") return url;
  }} catch (err) {{}}
  return "";
}}

function renderHeader() {{
  const name = board.user_name ? ", " + board.user_name : "";
  document.getElementById("title").textContent = (board.mode === "eod" ? strings.eod_title : strings.greeting) + name + " · " + board.date;
  document.getElementById("reset").textContent = strings.reset;
  const pills = document.getElementById("pills");
  pills.replaceChildren();
  const all = el("button", strings.filter_all, "pill");
  all.type = "button";
  all.setAttribute("aria-pressed", filter === "all" ? "true" : "false");
  all.addEventListener("click", () => {{ filter = "all"; render(); }});
  pills.appendChild(all);
  board.sources.forEach((source) => {{
    const pill = el("button", source, "pill");
    pill.type = "button";
    pill.setAttribute("aria-pressed", filter === source ? "true" : "false");
    pill.addEventListener("click", () => {{ filter = source; render(); }});
    pills.appendChild(pill);
  }});
  const focus = document.getElementById("focus");
  focus.replaceChildren();
  if (board.mode === "morning" && board.focus.length) {{
    focus.appendChild(el("strong", strings.focus));
    board.focus.forEach((title) => focus.appendChild(el("span", title, "badge b-red")));
  }}
}}

function visible(card) {{
  return filter === "all" || card.source_label === filter || (!card.source_label && filter === "all");
}}

function cardNode(card) {{
  const node = el("article", null, "card" + (card.column === "done" ? " done" : ""));
  node.dataset.id = card.id;
  const bar = el("div");
  const handle = el("span", "⠿", "handle");
  handle.addEventListener("mousedown", (event) => startDrag(event, card, node));
  const remove = el("button", "✕", "delete");
  remove.type = "button";
  remove.setAttribute("aria-label", strings.delete);
  remove.addEventListener("click", () => {{
    cards = cards.filter((item) => item.id !== card.id);
    persist();
    render();
  }});
  bar.append(handle, remove);
  node.appendChild(bar);
  node.appendChild(el("div", card.title));
  const badges = el("div", null, "badges");
  if (card.source_label) badges.appendChild(el("span", card.source_label, "badge " + (sourceClass[card.source_type] || "b-gray")));
  badges.appendChild(el("span", card.priority, "badge " + (priorityClass[card.priority] || "b-gray")));
  if (card.tentative) badges.appendChild(el("span", strings.tentative, "badge b-amber"));
  if (card.overlap_with) badges.appendChild(el("span", strings.overlap + ": " + card.overlap_with, "badge b-red"));
  node.appendChild(badges);
  const href = safeHref(card.url || "");
  if (href) {{
    const link = el("a", strings.open + " ↗");
    link.href = href;
    link.rel = "noreferrer noopener";
    link.target = "_blank";
    node.appendChild(link);
  }}
  if (card.meta) node.appendChild(el("div", card.meta));
  return node;
}}

function addForm(column) {{
  const form = el("form", null, "add-form");
  const input = document.createElement("input");
  input.maxLength = 180;
  input.setAttribute("aria-label", strings.add);
  const select = document.createElement("select");
  ["urgent", "medium", "strategic", "event", "general"].forEach((priority) => {{
    const option = el("option", priority);
    option.value = priority;
    select.appendChild(option);
  }});
  const submit = el("button", "+");
  submit.type = "submit";
  form.append(input, select, submit);
  form.addEventListener("submit", (event) => {{
    event.preventDefault();
    const title = input.value.trim();
    if (!title) return;
    cards.push({{
      id: "manual-" + Date.now(),
      title: title.slice(0, 180),
      column,
      priority: select.value,
      source_type: "manual",
      source_label: "Manual",
      url: "",
      meta: "",
      tentative: false,
      overlap_with: ""
    }});
    persist();
    render();
  }});
  return form;
}}

function renderBoard() {{
  const app = document.getElementById("app");
  app.replaceChildren();
  if (board.mode === "eod") {{
    const sections = [
      ["accomplished", board.eod.accomplished.map((title) => ({{ title }}))],
      ["carryover", board.eod.carryover],
      ["tomorrow", board.eod.tomorrow_top3.map((title) => ({{ title }}))]
    ];
    sections.forEach(([key, items]) => {{
      const section = el("section", null, "section");
      section.appendChild(el("h2", strings[key]));
      if (!items.length) section.appendChild(el("p", "—"));
      items.forEach((item) => section.appendChild(el("p", item.title)));
      app.appendChild(section);
    }});
    app.appendChild(el("p", strings.carryover_help));
    const box = document.createElement("textarea");
    box.readOnly = true;
    box.value = JSON.stringify({{
      schema: "morning-briefing-carryover/1",
      date: board.date,
      cards: board.eod.carryover
    }}, null, 2);
    app.appendChild(box);
    return;
  }}
  if (!cards.length) {{
    app.appendChild(el("p", strings.empty));
    return;
  }}
  const columns = el("div", null, "columns");
  columnOrder.forEach((column) => {{
    const members = cards.filter((card) => card.column === column && visible(card));
    const wrap = el("section", null, "column");
    wrap.dataset.column = column;
    wrap.appendChild(el("h2", strings[column] + " (" + members.length + ")"));
    members.forEach((card) => wrap.appendChild(cardNode(card)));
    wrap.appendChild(addForm(column));
    wrap.addEventListener("mousemove", (event) => moveDrag(event, wrap));
    wrap.addEventListener("mouseup", (event) => dropDrag(event, column, wrap));
    columns.appendChild(wrap);
  }});
  app.appendChild(columns);
}}

function startDrag(event, card, node) {{
  if (board.mode !== "morning") return;
  event.preventDefault();
  const ghost = node.cloneNode(true);
  ghost.classList.add("ghost");
  document.body.appendChild(ghost);
  drag = {{ card, ghost, node }};
  node.style.opacity = "0.35";
}}

function moveDrag(event, wrap) {{
  if (!drag) return;
  drag.ghost.style.left = event.clientX + 8 + "px";
  drag.ghost.style.top = event.clientY + 8 + "px";
  wrap.querySelectorAll(".card").forEach((card) => card.classList.remove("over"));
  const target = event.target.closest ? event.target.closest(".card") : null;
  if (target) target.classList.add("over");
}}

function dropDrag(event, column, wrap) {{
  if (!drag) return;
  const target = event.target.closest ? event.target.closest(".card") : null;
  const moving = drag.card;
  cards = cards.filter((card) => card.id !== moving.id);
  moving.column = column;
  if (target && target.dataset.id) {{
    const index = cards.findIndex((card) => card.id === target.dataset.id);
    cards.splice(index < 0 ? cards.length : index, 0, moving);
  }} else {{
    cards.push(moving);
  }}
  drag.ghost.remove();
  drag = null;
  persist();
  render();
}}

function render() {{
  renderHeader();
  renderBoard();
}}

document.getElementById("reset").addEventListener("click", () => {{
  localStorage.removeItem(storageKey);
  cards = board.cards.slice();
  render();
}});
document.addEventListener("mouseup", () => {{
  if (!drag) return;
  drag.ghost.remove();
  drag = null;
  render();
}});
render();
</script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a morning briefing HTML board")
    parser.add_argument("--input", required=True, help="Path to the briefing JSON payload")
    parser.add_argument("--output", required=True, help="Path to the HTML file to write")
    args = parser.parse_args(argv)
    with open(args.input, encoding="utf-8") as handle:
        payload = json.load(handle)
    html = render(payload)
    with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(html)
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
