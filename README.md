# Turn one idea into a decision with explicit assumptions and stop conditions.

*Part of the [Vivaminima tools](https://github.com/vivaminima) for Claude Code users.*

<img src="https://raw.githubusercontent.com/vivaminima/vivaminima/main/img/run/go-no-go-verdict-skill.png" width="760" alt="go-no-go-verdict-skill: real output of the free version on a made-up sample">

**Install in Claude Code:** `/plugin install go-no-go-verdict --marketplace vivaminima/vivaminima`
A Claude Code skill and a small checker: eight sections that may not be skipped or reordered, every number tagged as observed, assumption or to check, and a stop date before the verdict.

## New to this? Start here

**Who it's for:** you have an idea (a product, a side project, a feature) and want a written yes or no before you spend a week on it. Works with Claude Code, including the Code tab of the Claude desktop app.

**You don't need to know Python.** Claude writes the document and runs the checker for you.

1. Download this repository (green **Code** button → **Download ZIP**) and unzip it anywhere.
2. Copy the `go-no-go-verdict` folder into your skills folder (the commands are under **Install** below). Or ask Claude: *"Copy the go-no-go-verdict folder from this download into my skills folder."*
3. Start a new Claude Code session.
4. Type: *"Go or no-go on this idea: (one or two sentences about your idea)"*

What you get back: one Markdown document with eight sections in a fixed order, every number marked as observed, assumption or to check, a stop date, and a verdict (`Go`, `Fix-then-go` or `No-go`) with the first step.

**Go/No-Go Verdict skill 1.0.0** - free, MIT.

Say **"go or no-go on this idea"**, **"should I build this"** or **"이 아이디어 판정해 줘"** in Claude Code. Claude
writes one Markdown document and runs the checker on it until it passes:

```
Go/No-Go Verdict check 1.0.0
File: example-verdict.md
Sections: 8 of 8
Verdict: Fix-then-go | stop date: 2026-12-15 | first step: Open the payment provider's fees page and fill in the two open lines of the price section.
Tags: observed 3, assumption 7, to check 2

PASS

7 of 12 tagged claims are assumptions. Counter-review brief, verdict ledger and assumption trend are in Pro.
```

(That is the real output for `go-no-go-verdict/example-verdict.md`, a made-up idea with made-up numbers.)

## The eight sections

| # | Section | The question it will not let you skip |
|---|---|---|
| 1 | New artifact | Does something new exist when this is done? |
| 2 | First buyer | Which one person - not which segment? |
| 3 | Channel | Where do they find it, and how do they pay? |
| 4 | Price and fees | What is the price, and what does every fee say on the official page? Unknown fees are `[to check]`, never a guess |
| 5 | Time | How many hours of work, in hours? |
| 6 | Blockers to first revenue | What stands between "built" and "first payment"? |
| 7 | Cap and stop conditions | What is the most you will spend, and on which date do you stop? |
| 8 | Verdict | `Go`, `Fix-then-go` or `No-go` - and the first step |

Every number carries `[observed: source]`, `[assumption]` or `[to check]` in the same paragraph, list item or
table row. Dates (YYYY-MM-DD), numbers in code, links and names such as `v2` need no tag.

## Install

The skill is the `go-no-go-verdict` folder. Copy it into your skills folder:

Windows (PowerShell):

```
Copy-Item -Recurse -Force .\go-no-go-verdict "$env:USERPROFILE\.claude\skills\"
```

macOS / Linux:

```
mkdir -p ~/.claude/skills
cp -R go-no-go-verdict ~/.claude/skills/
```

Start a new Claude Code session. To use it in one project only, copy the folder into that project's
`.claude/skills/` instead. To remove it, delete the folder. Python 3.8 or newer is needed for the checker;
nothing else to install.

## Use the checker on its own

```
python go-no-go-verdict/check_verdict.py my-verdict.md
python go-no-go-verdict/check_verdict.py my-verdict.md --format json
```

(`python3` on macOS and Linux.) Start from `go-no-go-verdict/template.md`.

| Code | Meaning |
|---|---|
| `SECTION_MISSING`, `SECTION_ORDER`, `SECTION_EMPTY` | A section is not there, is out of order or repeated, or has no answer yet |
| `NUMBER_UNTAGGED` | A number without one of the three tags |
| `OBSERVED_NO_SOURCE` | `[observed]` without saying where it was seen |
| `FEE_ASSUMED` | A fee, commission or tax tagged `[assumption]` in section 4 |
| `TIME_NOT_IN_HOURS` | Section 5 has no time in hours |
| `STOP_DATE_MISSING` | Section 7 has no valid YYYY-MM-DD date |
| `VERDICT_MISSING`, `FIRST_STEP_MISSING` | Section 8 lacks one of the three verdicts, or the first step |
| `SECTION_TITLE`, `TITLE_MISSING` | Warnings: a section or the document is not titled as in the template |

Exit codes: `0` pass, `1` errors found, `2` the file could not be read. The checker only reads the file.

## Limits

- It checks the form: sections, tags, dates, units. It cannot tell whether an observation is true or an
  assumption is reasonable. A verdict that passes can still be wrong.
- A tag covers its whole paragraph, list item or table row. Two numbers in one item share one tag.
- English section titles and tag words. The text inside the sections can be in any language.
- The skill asks Claude to keep the order and tag every number; the checker is what enforces it. If you write
  the document by hand, run the checker yourself.

## Tested

Windows 11, Python 3.10.11: 30 tests, including a cp949 console run. Other versions and platforms have not
been tested. Run them with `python -m unittest discover -s tests`.

MIT licence. See CHANGELOG.md.

## More from Vivaminima

- **Go/No-Go Verdict Pro ($19)**, the paid edition of this tool, one-time payment on Gumroad: https://vivastory4.gumroad.com/l/go-no-go-verdict-pro

  <a href="https://vivastory4.gumroad.com/l/go-no-go-verdict-pro"><img src="https://raw.githubusercontent.com/vivaminima/vivaminima/main/img/go-no-go-verdict-skill.png" width="480" alt="Go/No-Go Verdict Pro"></a>

- **Token Audit Kit ($19)** — see how many tokens your CLAUDE.md and its @imports cost before your first prompt, and a step-by-step guide to split it. Free script: https://github.com/vivaminima/context-file-audit · Paid kit (store): https://vivastory4.gumroad.com
- Free tools: [skill-audit-kit](https://github.com/vivaminima/skill-audit-kit) · [secret-map](https://github.com/vivaminima/secret-map) · [inbox-ledger](https://github.com/vivaminima/inbox-ledger) · [release-gate](https://github.com/vivaminima/release-gate) · [skill-install-gate](https://github.com/vivaminima/skill-install-gate) · [console-safe](https://github.com/vivaminima/console-safe) · [checklist-stop](https://github.com/vivaminima/checklist-stop) · [handoff-check](https://github.com/vivaminima/handoff-check) · [llm-budget-router-lite](https://github.com/vivaminima/llm-budget-router-lite) · [go-no-go-verdict-skill](https://github.com/vivaminima/go-no-go-verdict-skill) · [ai-company-starter-kit](https://github.com/vivaminima/ai-company-starter-kit) · [beginner-readme-section](https://github.com/vivaminima/beginner-readme-section)

Vivaminima is not affiliated with, endorsed by or sponsored by Anthropic.
