# Changelog

## 1.0.0
First release.

- Claude Code skill `go-no-go-verdict`: one decision document per idea, eight sections in a fixed order (new
  artifact, first buyer, channel, price and fees, time in hours, blockers, cap and stop conditions, verdict).
- Every number is tagged `[observed: source]`, `[assumption]` or `[to check]`.
- `check_verdict.py`: reports missing, reordered and empty sections, untagged numbers, a fee tagged as an
  assumption, time not in hours, a missing stop date, a missing verdict or first step. Text and JSON output.
- `template.md` and `example-verdict.md` (a made-up idea).
- 30 tests.
