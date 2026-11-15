#!/usr/bin/env python3
"""Check a go/no-go verdict document: every section there, in order, and every number tagged.

  check_verdict.py VERDICT.md [--format text|json]

A verdict has eight sections, in this order, as "## N. Title" headings:
  1 New artifact   2 First buyer   3 Channel   4 Price and fees   5 Time
  6 Blockers to first revenue   7 Cap and stop conditions   8 Verdict

Every number must carry one of [observed: source], [assumption] or [to check] in the same
paragraph, list item or table row. Read-only. Standard library only. No network.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

VERSION = "1.0.0"
TOOL = "Go/No-Go Verdict check"
SECTIONS = [(1, "New artifact", "artifact"), (2, "First buyer", "buyer"), (3, "Channel", "channel"),
            (4, "Price and fees", "price"), (5, "Time", "time"), (6, "Blockers to first revenue", "block"),
            (7, "Cap and stop conditions", "stop"), (8, "Verdict", "verdict")]
VERDICTS = ("Go", "Fix-then-go", "No-go")

HEADING = re.compile(r"^##\s*(\d+)\s*[.)]\s*(.*?)\s*#*\s*$")
TAG = re.compile(r"\[\s*(observed|assumption|to check)\s*(?::\s*([^\]]*))?\]", re.I)
ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
NUMBER = re.compile(r"(?<![A-Za-z0-9_])(?<![A-Za-z]-)\d[\d,]*(?:\.\d+)?")
HOURS = re.compile(r"\d[\d,]*(?:\.\d+)?\s*(?:h|hr|hrs|hours?)\b", re.I)
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
VERDICT_LINE = re.compile(r"verdict\W{0,6}(go|fix-then-go|no-go)\b", re.I)
FIRST_STEP = re.compile(r"first step\s*[:\-]\s*(.*)", re.I)
FEE_WORDS = re.compile(r"\b(?:fees?|commission|cut|tax|taxes|vat|payout|processing|surcharge)\b", re.I)
PLACEHOLDER = re.compile(r"^[\s.\-_*>]*(?:todo|tbd|\.\.\.)?[\s.\-_*]*$", re.I)


def read_text(path):
    raw = Path(path).read_bytes()
    for bom, codec in ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be")):
        if raw.startswith(bom):
            return raw[len(bom):].decode(codec)
    return raw.decode("utf-8")


def visible_lines(text):
    """(line number, text) with fenced code blocks and <!-- comments --> blanked out."""
    out, fence, comment = [], None, False
    for number, line in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), 1):
        stripped = line.strip()
        if fence:
            if stripped.startswith(fence):
                fence = None
            out.append((number, ""))
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            out.append((number, ""))
            continue
        kept = ""
        while line:
            if comment:
                end = line.find("-->")
                if end < 0:
                    line = ""
                else:
                    line, comment = line[end + 3:], False
            else:
                start = line.find("<!--")
                if start < 0:
                    kept, line = kept + line, ""
                else:
                    kept, line, comment = kept + line[:start], line[start + 4:], True
        out.append((number, kept))
    return out


def bare(text):
    """The text with everything that may hold a digit without being a claim removed."""
    text = TAG.sub(" ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"\b[a-z][a-z0-9+.-]*://\S+", " ", text, flags=re.I)
    text = ISO_DATE.sub(" ", text)
    return LIST_ITEM.sub("", text, count=1)


def blocks_of(lines):
    """Group lines into claims: a paragraph, one list item (with its wrapped lines) or one table row."""
    blocks, current = [], []
    for number, text in lines:
        if not text.strip():
            if current:
                blocks.append(current)
            current = []
            continue
        if current and (LIST_ITEM.match(text) or text.lstrip().startswith("|")):
            blocks.append(current)
            current = []
        current.append((number, text))
    if current:
        blocks.append(current)
    return blocks


def analyze(text):
    """Return the facts and findings of one verdict document."""
    lines = visible_lines(text)
    findings = []

    def add(severity, code, line, message):
        findings.append({"severity": severity, "code": code, "line": line, "message": message})

    title = None
    heads = []                                           # (section number, line number, title)
    for number, line in lines:
        if title is None and re.match(r"^#\s+\S", line):
            title = re.sub(r"^#\s+(?:verdict\s*[:\-]\s*)?", "", line, flags=re.I).strip()
        match = HEADING.match(line)
        if match:
            heads.append((int(match.group(1)), number, match.group(2)))
    if not title:
        add("warning", "TITLE_MISSING", 1, "Start with a title line: '# Verdict: <the idea in a few words>'")

    order = [h[0] for h in heads]
    if order != sorted(order) or len(set(order)) != len(order):
        add("error", "SECTION_ORDER", heads[0][1] if heads else 1,
            "Sections must come in order 1 to 8, each once (found: %s)" % (", ".join(str(n) for n in order) or "none"))
    bodies = {}
    for index, (section, line, _title) in enumerate(heads):
        end = heads[index + 1][1] if index + 1 < len(heads) else lines[-1][0] + 1
        bodies.setdefault(section, (line, [(n, t) for n, t in lines if line < n < end]))
    for section, name, keyword in SECTIONS:
        if section not in bodies:
            add("error", "SECTION_MISSING", 1, "Section %d (%s) is missing: add a '## %d. %s' heading"
                % (section, name, section, name))
            continue
        line, body = bodies[section]
        head_title = [h[2] for h in heads if h[0] == section][0]
        if keyword not in head_title.lower():
            add("warning", "SECTION_TITLE", line, "Section %d should be titled '%s' (found '%s')"
                % (section, name, head_title))
        if all(PLACEHOLDER.match(t) for _n, t in body):
            add("error", "SECTION_EMPTY", line, "Section %d (%s) has no answer yet" % (section, name))

    tags = {"observed": 0, "assumption": 0, "to check": 0}
    assumptions, to_checks = [], []
    for section in sorted(bodies):
        _line, body = bodies[section]
        for block in blocks_of(body):
            joined = " ".join(t.strip() for _n, t in block)
            found = [(m.group(1).lower(), (m.group(2) or "").strip()) for m in TAG.finditer(joined)]
            for kind, source in found:
                tags[kind] += 1
                if kind == "observed" and not source:
                    add("error", "OBSERVED_NO_SOURCE", block[0][0],
                        "[observed] needs its source: [observed: where you saw it]")
                if kind == "assumption" and section == 4 and FEE_WORDS.search(joined):
                    add("error", "FEE_ASSUMED", block[0][0],
                        "Fees come from the official page only: use [observed: page] or [to check], "
                        "not [assumption]")
            if any(k == "assumption" for k, _s in found):
                assumptions.append({"line": block[0][0], "section": section, "text": joined})
            if any(k == "to check" for k, _s in found):
                to_checks.append({"line": block[0][0], "section": section, "text": joined})
            if not found:
                for number, text in block:
                    hit = NUMBER.search(bare(text))
                    if hit:
                        add("error", "NUMBER_UNTAGGED", number,
                            "The number %s has no tag: add [observed: source], [assumption] or [to check]" % hit.group(0))
                        break

    verdict = stop_date = first_step = None
    if 5 in bodies and not any(HOURS.search(t) for _n, t in bodies[5][1]) and \
            not all(PLACEHOLDER.match(t) for _n, t in bodies[5][1]):
        add("error", "TIME_NOT_IN_HOURS", bodies[5][0], "Section 5 gives the work time in hours, e.g. '6 h [assumption]'")
    if 7 in bodies:
        for _n, t in bodies[7][1]:
            for match in ISO_DATE.finditer(TAG.sub(" ", t)):
                try:
                    stop_date = stop_date or datetime.date(*[int(g) for g in match.groups()]).isoformat()
                except ValueError:
                    pass
        if not stop_date and not all(PLACEHOLDER.match(t) for _n, t in bodies[7][1]):
            add("error", "STOP_DATE_MISSING", bodies[7][0],
                "Section 7 needs the date you stop on, written as YYYY-MM-DD")
    if 8 in bodies:
        for _n, t in bodies[8][1]:
            plain = t.replace("*", "").replace("_", "")
            match = VERDICT_LINE.search(plain)
            if match and verdict is None:
                verdict = [v for v in VERDICTS if v.lower() == match.group(1).lower()][0]
            match = FIRST_STEP.search(plain)
            if match and first_step is None and re.search(r"\w", TAG.sub("", match.group(1))) and \
                    not PLACEHOLDER.match(match.group(1)):
                first_step = TAG.sub("", match.group(1)).strip()
        if not all(PLACEHOLDER.match(t) for _n, t in bodies[8][1]):
            if verdict is None:
                add("error", "VERDICT_MISSING", bodies[8][0],
                    "Section 8 needs a line 'Verdict: Go', 'Verdict: Fix-then-go' or 'Verdict: No-go'")
            if first_step is None:
                add("error", "FIRST_STEP_MISSING", bodies[8][0], "Section 8 needs a line 'First step: ...'")

    findings.sort(key=lambda f: (f["line"], f["code"]))
    total = sum(tags.values())
    return {"title": title, "sections_found": sorted(set(order) & {s[0] for s in SECTIONS}), "verdict": verdict,
            "stop_date": stop_date, "first_step": first_step, "tags": tags, "tagged": total,
            "assumption_pct": round(100.0 * tags["assumption"] / total, 1) if total else 0.0,
            "assumptions": assumptions, "to_checks": to_checks, "findings": findings,
            "ok": not any(f["severity"] == "error" for f in findings)}


def pro_tools_present():
    return (Path(__file__).resolve().parent / "counter_review.py").is_file()


def closing_line(result):
    """One closing line with the real numbers. Nothing when there is no assumption, or in the Pro package."""
    n = result["tags"]["assumption"]
    if not n or pro_tools_present():
        return None
    return ("%d of %d tagged claims %s. Counter-review brief, verdict ledger and assumption "
            "trend are in Pro." % (n, result["tagged"], "is an assumption" if n == 1 else "are assumptions"))


def render_text(result, name):
    errors = sum(1 for f in result["findings"] if f["severity"] == "error")
    warnings = len(result["findings"]) - errors
    lines = ["%s %s" % (TOOL, VERSION), "File: %s" % name,
             "Sections: %d of %d" % (len(result["sections_found"]), len(SECTIONS)),
             "Verdict: %s | stop date: %s | first step: %s" % (result["verdict"] or "-", result["stop_date"] or "-",
                                                             result["first_step"] or "-"),
             "Tags: observed %d, assumption %d, to check %d" % (result["tags"]["observed"], result["tags"]["assumption"],
                                                               result["tags"]["to check"]), ""]
    for f in result["findings"]:
        lines.append("  line %d  %s %s: %s" % (f["line"], "ERROR  " if f["severity"] == "error" else "WARNING",
                                              f["code"], f["message"]))
    if result["findings"]:
        lines.append("")
    lines.append("PASS" + (" with %d warning(s)" % warnings if warnings else "") if result["ok"]
                 else "FAIL: %d error(s)%s" % (errors, ", %d warning(s)" % warnings if warnings else ""))
    line = closing_line(result)
    if line:
        lines += ["", line]
    return "\n".join(lines)


def safe_stdio():
    """Never crash on a console that cannot show a character (cp949, ascii): replace it instead."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and (stream.encoding or "").lower().replace("-", "").replace("_", "") != "utf8":
                stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def load(path):
    """Return (text, error message)."""
    path = Path(path)
    if not path.is_file():
        return None, "file not found: %s" % path.name
    try:
        return read_text(path), None
    except UnicodeDecodeError:
        return None, "%s is not UTF-8 text" % path.name
    except OSError as exc:
        return None, "cannot read %s (%s)" % (path.name, type(exc).__name__)


def main(argv=None):
    safe_stdio()
    parser = argparse.ArgumentParser(prog="check_verdict", description="Check a go/no-go verdict document.")
    parser.add_argument("file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--version", action="version", version="%s %s" % (TOOL, VERSION))
    args = parser.parse_args(argv)
    text, error = load(args.file)
    if error:
        print("ERROR: %s" % error, file=sys.stderr)
        return 2
    result = analyze(text)
    if args.format == "json":
        print(json.dumps(dict(result, file=Path(args.file).name, tool=TOOL, version=VERSION), ensure_ascii=False, indent=2))
    else:
        print(render_text(result, Path(args.file).name))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
