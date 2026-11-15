"""Tests for the Go/No-Go Verdict skill checker. Run:  python -m unittest discover -s tests"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
SKILL = PKG / "go-no-go-verdict"
ENGINE = SKILL / "engine" if (SKILL / "engine").is_dir() else SKILL
sys.path.insert(0, str(ENGINE))
import check_verdict as cv

GOOD = (SKILL / "example-verdict.md").read_text(encoding="utf-8")


def codes(text):
    return [f["code"] for f in cv.analyze(text)["findings"]]


def section(text, number):
    """The text of one section, heading included."""
    match = re.search(r"(?ms)^## %d\..*?(?=^## \d\.|\Z)" % number, text)
    return match.group(0)


class Example(unittest.TestCase):
    def test_shipped_example_passes(self):
        result = cv.analyze(GOOD)
        self.assertEqual(result["findings"], [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["sections_found"], [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual((result["verdict"], result["stop_date"]), ("Fix-then-go", "2026-12-15"))
        self.assertTrue(result["first_step"].startswith("Open the payment provider's fees page"))
        self.assertEqual(result["tags"], {"observed": 3, "assumption": 7, "to check": 2})
        self.assertEqual(result["assumption_pct"], 58.3)
        self.assertEqual(result["title"], "Invoice reminder script for freelance designers")

    def test_shipped_template_fails_until_it_is_filled_in(self):
        found = codes((SKILL / "template.md").read_text(encoding="utf-8"))
        self.assertEqual(found.count("SECTION_EMPTY"), 7)
        self.assertIn("VERDICT_MISSING", found)
        self.assertIn("FIRST_STEP_MISSING", found)


class Sections(unittest.TestCase):
    def test_each_missing_section_is_named(self):
        for number in range(1, 9):
            found = cv.analyze(GOOD.replace(section(GOOD, number), ""))["findings"]
            missing = [f for f in found if f["code"] == "SECTION_MISSING"]
            self.assertEqual(len(missing), 1, number)
            self.assertIn("Section %d " % number, missing[0]["message"])

    def test_skipping_ahead_to_the_verdict_is_caught(self):
        moved = GOOD.replace(section(GOOD, 8), "").replace(section(GOOD, 2), section(GOOD, 8) + section(GOOD, 2))
        self.assertIn("SECTION_ORDER", codes(moved))

    def test_duplicate_section_is_caught(self):
        self.assertIn("SECTION_ORDER", codes(GOOD + "\n" + section(GOOD, 3)))

    def test_empty_and_placeholder_sections_are_caught(self):
        for filler in ("", "TODO", "...", "<!-- later -->", "-"):
            text = GOOD.replace(section(GOOD, 6), "## 6. Blockers to first revenue\n\n%s\n\n" % filler)
            self.assertIn("SECTION_EMPTY", codes(text), filler)

    def test_wrong_title_is_a_warning_not_an_error(self):
        result = cv.analyze(GOOD.replace("## 3. Channel", "## 3. Marketing"))
        self.assertEqual([f["code"] for f in result["findings"]], ["SECTION_TITLE"])
        self.assertTrue(result["ok"])


class Numbers(unittest.TestCase):
    def one(self, line):
        text = GOOD.replace("- I expect 40 visitors from the first post [assumption].", line)
        return [f for f in cv.analyze(text)["findings"] if f["code"] == "NUMBER_UNTAGGED"]

    def test_untagged_number_is_caught_with_its_line(self):
        found = self.one("- I expect 40 visitors from the first post.")
        self.assertEqual(len(found), 1)
        self.assertIn("The number 40 has no tag", found[0]["message"])
        self.assertEqual(GOOD.split("\n")[found[0]["line"] - 1][:11], "- I expect ")

    def test_money_percent_and_decimals_count_as_numbers(self):
        for line in ("- Churn rate 2.5% expected.", "- Costs $1,200 a year.", "- Takes 3 tries."):
            self.assertEqual(len(self.one(line)), 1, line)

    def test_any_of_the_three_tags_is_enough(self):
        for tag in ("[observed: forum stats page]", "[assumption]", "[to check]", "[ASSUMPTION]", "[To Check]"):
            self.assertEqual(self.one("- I expect 40 visitors %s." % tag), [], tag)

    def test_tag_may_sit_on_a_wrapped_line_of_the_same_item_but_not_in_the_next_item(self):
        self.assertEqual(self.one("- I expect 40 visitors\n  from the first post [assumption]."), [])
        self.assertEqual(len(self.one("- I expect 40 visitors.\n- Most are designers [assumption].")), 1)

    def test_things_that_are_not_claims_need_no_tag(self):
        for line in ("- Launch on 2026-12-01.", "- See `retry=3` in the config.", "- Uses the v2 API and GPT-4 style names.",
                     "1. First do the page.", "- Read https://example.org/page/42 first.", "- SKU01 is the name."):
            self.assertEqual(self.one(line), [], line)

    def test_numbers_inside_code_blocks_and_comments_are_ignored(self):
        self.assertEqual(self.one("```\nprice = 99\n```\n<!-- maybe 500 buyers -->"), [])

    def test_observed_needs_a_source(self):
        text = GOOD.replace("[observed: her message to me, 2026-10-28]", "[observed]")
        self.assertIn("OBSERVED_NO_SOURCE", codes(text))

    def test_table_rows_are_checked_one_by_one(self):
        table = "| item | hours |\n|---|---|\n| page | 2 [assumption] |\n| script | 6 |"
        found = self.one(table)
        self.assertEqual(len(found), 1)
        self.assertIn("The number 6", found[0]["message"])


class Rules(unittest.TestCase):
    def test_fee_tagged_as_assumption_is_an_error_but_your_own_price_is_not(self):
        text = GOOD.replace("- Payment provider fee per sale: [to check] on the provider's official fees page before launch.",
                            "- Payment provider fee per sale: 5% [assumption].")
        self.assertEqual(codes(text), ["FEE_ASSUMED"])
        self.assertNotIn("FEE_ASSUMED", codes(GOOD))                        # "Price: 15 dollars [assumption]" is fine

    def test_time_must_be_in_hours(self):
        text = GOOD.replace("6 h of agent working time", "about a week of work").replace("setup: 2 h", "setup: half a day")
        self.assertIn("TIME_NOT_IN_HOURS", codes(text))
        self.assertNotIn("TIME_NOT_IN_HOURS", codes(GOOD.replace("6 h of", "6 hours of")))

    def test_stop_condition_needs_a_date(self):
        self.assertIn("STOP_DATE_MISSING", codes(GOOD.replace("Stop on 2026-12-15 if", "Stop next month if")))
        self.assertIn("STOP_DATE_MISSING", codes(GOOD.replace("2026-12-15", "2026-13-45")))

    def test_verdict_must_be_one_of_three_and_come_with_a_first_step(self):
        self.assertIn("VERDICT_MISSING", codes(GOOD.replace("Verdict: Fix-then-go", "Verdict: Maybe")))
        self.assertIn("FIRST_STEP_MISSING", codes(re.sub(r"First step:.*", "First step:", GOOD)))
        for word in ("Go", "No-go", "Fix-then-go", "**No-go**", "go"):
            result = cv.analyze(GOOD.replace("Verdict: Fix-then-go", "Verdict: " + word))
            self.assertTrue(result["ok"], word)
            self.assertIn(result["verdict"], cv.VERDICTS)

    def test_title_is_asked_for(self):
        self.assertIn("TITLE_MISSING", codes(GOOD.replace("# Verdict: Invoice reminder script for freelance designers", "")))


class Cli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cv.main([str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def test_pass_fail_and_missing_file_exit_codes(self):
        self.assertEqual(self.run_main(SKILL / "example-verdict.md")[0], 0)
        bad = self.root / "bad verdict 판정.md"
        bad.write_text(GOOD.replace("[assumption]", ""), encoding="utf-8")
        code, out, _ = self.run_main(bad)
        self.assertEqual(code, 1)
        self.assertIn("FAIL: 7 error(s)", out)
        self.assertNotIn(str(self.root), out)                                # the file name only, never the folder
        code, out, err = self.run_main(self.root / "none.md")
        self.assertEqual(code, 2)
        self.assertIn("file not found: none.md", err)

    def test_closing_line_has_the_real_numbers_and_only_in_the_free_package(self):
        code, out, _ = self.run_main(SKILL / "example-verdict.md")
        line = "7 of 12 tagged claims are assumptions. Counter-review brief, verdict ledger and assumption trend are in Pro."
        if cv.pro_tools_present():
            self.assertNotIn("are in Pro", out)
        else:
            self.assertTrue(out.rstrip().endswith(line), out)

    def test_no_closing_line_without_assumptions(self):
        clean = self.root / "v.md"
        clean.write_text(GOOD.replace("[assumption]", "[to check]"), encoding="utf-8")
        code, out, _ = self.run_main(clean)
        self.assertEqual(code, 0)
        self.assertNotIn("Pro", out)
        self.assertTrue(out.rstrip().endswith("PASS"))

    def test_json_output(self):
        code, out, _ = self.run_main(SKILL / "example-verdict.md", "--format", "json")
        data = json.loads(out)
        self.assertEqual((data["ok"], data["file"], data["verdict"], len(data["assumptions"])), (True, "example-verdict.md",
                                                                                                 "Fix-then-go", 7))

    def test_bom_crlf_and_utf16_files_are_read(self):
        for name, raw in (("bom.md", b"\xef\xbb\xbf" + GOOD.replace("\n", "\r\n").encode("utf-8")),
                          ("u16.md", b"\xff\xfe" + GOOD.encode("utf-16-le"))):
            (self.root / name).write_bytes(raw)
            self.assertEqual(self.run_main(self.root / name)[0], 0, name)
        (self.root / "bin.md").write_bytes(b"\x81\x82\x83\xff")
        self.assertEqual(self.run_main(self.root / "bin.md")[0], 2)

    def test_cp949_and_ascii_consoles_exit_cleanly(self):
        doc = self.root / "한글 판정.md"
        doc.write_text(GOOD.replace("Invoice reminder", "청구서 알림 – reminder"), encoding="utf-8")
        for enc in ("cp949", "ascii"):
            env = dict(os.environ, PYTHONIOENCODING=enc, PYTHONUTF8="0")
            r = subprocess.run([sys.executable, str(ENGINE / "check_verdict.py"), str(doc)], capture_output=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(b"PASS", r.stdout)


class Package(unittest.TestCase):
    def test_skill_frontmatter_and_trigger_phrases(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        head = text.split("---")[1]
        self.assertIn("name: go-no-go-verdict", head)
        description = re.search(r"description: (.*)", head).group(1)
        self.assertLessEqual(len(description), 1024)
        for phrase in ("Use when", "go or no-go", "should I build this", "판정해 줘"):
            self.assertIn(phrase, description)
        for n, (_i, name, _k) in enumerate(cv.SECTIONS, 1):
            self.assertIn("%d. **%s**" % (n, name), text)
        for tag in ("[observed: source]", "[assumption]", "[to check]"):
            self.assertIn(tag, text)
        self.assertLess(text.count("\n"), 500)

    def test_files_the_skill_points_at_exist(self):
        for name in ("template.md", "example-verdict.md", "ORIGIN.md"):
            self.assertTrue((SKILL / name).is_file(), name)
        self.assertTrue((ENGINE / "check_verdict.py").is_file())

    def test_checker_is_ascii_standard_library_and_offline(self):
        import ast
        source = (ENGINE / "check_verdict.py").read_text(encoding="utf-8")
        self.assertTrue(all(ord(c) < 128 for c in source))
        allowed = {"__future__", "argparse", "datetime", "json", "re", "sys", "pathlib"}
        for node in ast.walk(ast.parse(source)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                self.assertIn(name.split(".")[0], allowed)

    def test_readme_first_line_and_no_sales_copy(self):
        text = (PKG / "README.md").read_text(encoding="utf-8")
        first = text.split("\n")[0]
        if not cv.pro_tools_present():                                       # the free package's own first line
            self.assertEqual(first, "# Turn one idea into a decision with explicit assumptions and stop conditions.")
        low = text.lower()
        for word in ("re" + "fund", "money" + " back", "buy now", "http://", "https://"):
            self.assertNotIn(word, low)


if __name__ == "__main__":
    unittest.main()
