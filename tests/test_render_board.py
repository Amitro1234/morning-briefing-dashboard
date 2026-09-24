import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "morning-briefing" / "scripts" / "render_board.py"
SKILL = ROOT / "morning-briefing" / "SKILL.md"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_board", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_board = load_renderer()


def board_from_html(html: str) -> dict:
    start = html.index('<script type="application/json" id="board-data">') + len(
        '<script type="application/json" id="board-data">'
    )
    end = html.index("</script>", start)
    return json.loads(html[start:end])


class RenderBoardTests(unittest.TestCase):
    def test_escapes_markup_and_rejects_script_urls(self):
        html = render_board.render(
            {
                "mode": "morning",
                "date": "2026-09-24",
                "lang": "en",
                "cards": [
                    {
                        "title": '<script>alert("x")</script>',
                        "url": "javascript:alert(1)",
                        "column": "todo",
                        "priority": "urgent",
                        "source_type": "email",
                        "source_label": "Gmail",
                    }
                ],
            }
        )
        self.assertNotIn("<script>alert", html)
        board = board_from_html(html)
        self.assertEqual(board["cards"][0]["url"], "")
        self.assertIn("\\u003cscript\\u003e", html)

    def test_empty_payload_has_no_invented_cards(self):
        board = board_from_html(render_board.render({"mode": "morning", "date": "2026-09-24", "lang": "en", "cards": []}))
        self.assertEqual(board["cards"], [])
        self.assertIn("Paste Jira", board["strings"]["empty"])

    def test_caps_columns_and_sources_and_dedupes(self):
        cards = [
            {
                "id": f"t{i}",
                "title": f"Task {i}",
                "column": "todo",
                "priority": "general",
                "source_type": "tasks",
                "source_label": "Jira",
            }
            for i in range(6)
        ]
        cards.append(dict(cards[0], id="dup"))
        cards.extend(
            {
                "id": f"e{i}",
                "title": f"Mail {i}",
                "column": "todo",
                "priority": "medium",
                "source_type": "email",
                "source_label": "Outlook",
            }
            for i in range(12)
        )
        board = board_from_html(render_board.render({"mode": "morning", "date": "2026-09-24", "lang": "en", "cards": cards}))
        todo = [card for card in board["cards"] if card["column"] == "todo"]
        self.assertEqual(len(todo), 6)
        self.assertTrue(any(card["id"] == "grouped-todo" for card in todo))
        outlook = [card for card in board["cards"] if card["source_label"] == "Outlook"]
        self.assertLessEqual(len(outlook), 10)
        self.assertEqual(json.dumps(board).count("Task 0"), 1)

    def test_hebrew_user_text_sets_rtl_copy(self):
        html = render_board.render(
            {
                "mode": "morning",
                "date": "2026-09-24",
                "user_text": "מה יש לי היום",
                "cards": [{"title": "Review PR", "column": "todo", "source_type": "tasks", "source_label": "Linear"}],
            }
        )
        self.assertIn('dir="rtl"', html)
        self.assertIn("בוקר טוב", html)

    def test_overlap_and_eod_carryover(self):
        html = render_board.render(
            {
                "mode": "eod",
                "date": "2026-09-24",
                "lang": "en",
                "cards": [
                    {
                        "title": "Planning",
                        "column": "in_progress",
                        "priority": "event",
                        "source_type": "calendar",
                        "source_label": "Outlook Calendar",
                        "start": "2026-09-24T09:00:00+03:00",
                        "end": "2026-09-24T10:00:00+03:00",
                    },
                    {
                        "title": "Interview",
                        "column": "in_progress",
                        "priority": "event",
                        "source_type": "calendar",
                        "source_label": "Google Calendar",
                        "start": "2026-09-24T09:30:00+03:00",
                        "end": "2026-09-24T10:30:00+03:00",
                    },
                    {"title": "Closed ticket", "column": "done", "source_type": "tasks", "source_label": "Jira"},
                ],
            }
        )
        board = board_from_html(html)
        self.assertEqual(board["cards"][0]["overlap_with"], "Interview")
        self.assertEqual(board["eod"]["accomplished"], ["Closed ticket"])
        self.assertEqual(len(board["eod"]["carryover"]), 2)
        self.assertIn("End of day", html)

    def test_cli_writes_file(self):
        payload = {"mode": "morning", "date": "2026-09-24", "lang": "en", "cards": []}
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            source = folder / "in.json"
            target = folder / "out.html"
            source.write_text(json.dumps(payload), encoding="utf-8")
            code = render_board.main(["--input", str(source), "--output", str(target)])
            self.assertEqual(code, 0)
            self.assertIn("board-data", target.read_text(encoding="utf-8"))

    def test_skill_mentions_every_readme_source(self):
        skill = SKILL.read_text(encoding="utf-8")
        for phrase in [
            "Outlook",
            "Gmail",
            "Google Calendar",
            "Outlook Calendar",
            "Jira",
            "Linear",
            "Asana",
            "Notion",
            "Monday",
            "ClickUp",
            "GitHub",
            "GitLab",
            "Slack",
            "Teams",
            "Obsidian",
            "- [ ]",
            "- [/]",
            "- [x]",
        ]:
            self.assertIn(phrase, skill)

    def test_packaged_skill_matches_source(self):
        package = ROOT / "morning-briefing.skill"
        self.assertTrue(package.exists(), "run tools/package_skill.py")
        with zipfile.ZipFile(package) as archive:
            names = set(archive.namelist())
            self.assertIn("morning-briefing/SKILL.md", names)
            self.assertIn("morning-briefing/scripts/render_board.py", names)
            self.assertNotIn("zipDsHHF", names)
            packaged = archive.read("morning-briefing/SKILL.md")
            script = archive.read("morning-briefing/scripts/render_board.py")
        self.assertEqual(packaged, SKILL.read_bytes().replace(b"\r\n", b"\n"))
        self.assertEqual(script, SCRIPT.read_bytes().replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main()
