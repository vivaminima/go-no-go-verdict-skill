---
name: go-no-go-verdict
description: Turns one product or project idea into a written go/no-go decision with explicit assumptions and stop conditions - eight fixed sections (new artifact, first buyer, channel, price and fees, time in hours, blockers, cap and stop date, verdict and first step), every number tagged as observed, assumption or to check. Use when the user asks whether to build, launch or keep going with an idea, for example "should I build this", "go or no-go", "is this worth doing", "give me a verdict on this idea", "이 아이디어 판정해 줘", "할지 말지 정해 줘".
license: MIT
---

# Go/No-Go Verdict

Write one decision document for one idea. The value is in what the document refuses to skip:
every section is answered in order, every number says where it came from, and the decision
comes with the date on which the user stops.

## When to use

- The user has an idea (a product, a feature, a side project, a campaign) and wants a decision,
  not a brainstorm: "should I build this", "go or no-go", "이 아이디어 판정해 줘".
- The user wants to review an idea they already started and decide whether to continue.

Do not use it for open-ended research, for comparing many ideas at once, or when the user
only wants encouragement. One idea, one document.

## The eight sections - never skip, never reorder

Copy `template.md` from this skill's base directory and fill it in, in this order. If you
cannot answer a section, write what is missing and tag it `[to check]` - do not leave it out
and do not move on to the verdict first.

1. **New artifact** - Does this create something that does not exist yet (a file, a tool, a
   page a buyer can get)? Say what it is in one line. If nothing new is made, say so.
2. **First buyer** - One person, described well enough that the user could message them
   today. Not a market segment.
3. **Channel** - How that person finds it and how they pay. Name the store or payment tool
   and the place the first visitors come from.
4. **Price and fees** - The price, and every fee between the buyer's payment and the user's
   account. Fees come from the provider's official page only. If you have not seen the page in
   this conversation, write `[to check]` - never estimate a fee.
5. **Time** - Hours of work to the first sellable version, in hours. If an agent does the
   work, give agent working hours. Not days, not weeks.
6. **Blockers to first revenue** - What stands between "built" and "first payment": approvals,
   accounts, missing assets, anything only the user can do.
7. **Cap and stop conditions** - The most the user will spend (hours and money), and the
   condition and **date** (YYYY-MM-DD) on which they stop. A stop condition without a date is
   not a stop condition.
8. **Verdict** - One of `Go`, `Fix-then-go`, `No-go`, as a line `Verdict: ...`, then
   `First step: ...` - one action small enough to do today.

## Tag every number

Every number in the document carries exactly one of these tags, in the same paragraph, list
item or table row:

- `[observed: source]` - you or the user saw it. Name where: a page, a file, a message, a date.
- `[assumption]` - a guess. Guesses are allowed; hiding them is not.
- `[to check]` - not known yet and worth finding out before money or days are spent.

Do not turn an assumption into an observation by wording. If the user gives a number without
a source, ask where it comes from, or tag it `[assumption]`. Dates (YYYY-MM-DD) need no tag.

## Check before you hand it over

Save the verdict as a Markdown file, then run the checker from this skill's base directory:

```
python3 "<base directory>/check_verdict.py" verdict.md
```

(`python` or `py -3` on Windows.) It reports a missing or reordered section, an empty
section, a number without a tag, a fee tagged as an assumption, time not given in hours, a
missing stop date, and a missing verdict or first step. Fix what it reports and run it again
until it prints `PASS`. Exit code 0 means pass, 1 means errors.

## Tell the user

After `PASS`, reply with at most six lines:

1. The verdict and the first step.
2. The stop date and the stop condition.
3. How many claims are observed, assumed and still to check - the numbers the checker printed.
4. The one assumption that would change the verdict if it is wrong.

Do not soften a `No-go`. Do not add a section, a score or a table that the template does not
have. `example-verdict.md` shows a finished one (a made-up idea with made-up numbers).
