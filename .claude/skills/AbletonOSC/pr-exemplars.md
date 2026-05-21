# AbletonOSC — PR Archive & Exemplars

> Every merged PR is a record of what was contributed. Managed by `~/.claude/skills/pr-analysis.md`.

## Techniques Index

| Technique | First seen in | Category |
|-----------|--------------|----------|
| Property-list addition (no tests) | #143 | feature/expansion |
| Custom listener pattern with bug-fix test | #89 | bug-fix |
| Move endpoint to existing namespace | #153 (review) | refactor |
| Fixture-based clip creation for tests | tests/test_clip.py | testing |

---

## #143 — Introduce missing Clip properties (esaruoho, merged 2025-11-16)
**Files:** README.md, abletonosc/clip.py, run-console.py — 100/-32
**Pattern:** Append 14 names to `properties_r`/`properties_rw`. README table rows. Autocomplete strings in run-console.
**Tests:** None — property list-additions accepted without tests.
**Lesson:** Smallest possible diff focused on one mechanical thing. Got merged.

## #201 — DUPLICATE / CLOSED (esaruoho, 2026-05-21)
**Closed:** Same content as #143, opened from stale fork master. Diff would have reverted 4 months of upstream work.
**Lesson:** ALWAYS `git fetch origin && git diff origin/master` before opening a PR from a fork.

## #167 — Device Variations API (elzinko, open, CHANGES_REQUESTED)
**Maintainer ask:** Remove all new markdown files and `devel/` folder. Drop Live 12+ mentions. Keep the codebase lean.
**Lesson:** Don't ship docs/devnotes/extra files alongside a feature PR. Single-purpose.

## #153 — scroll_view handler (ltackett, open, CHANGES_REQUESTED)
**Maintainer ask:** Move from `/live/application/view/scroll_view` to `/live/view/scroll_view` — reuse existing namespace.
**Lesson:** Check existing namespaces before inventing nesting.

## #89 — Fix "Message too long" (StrongBearCeo, open)
**Maintainer added a test:** populates clip with ~384 notes and verifies round-trip. Test passes on master, fails with this PR's osc_server/client implementation → packet reassembly is broken.
**Lesson:** For protocol-level bugs, the test should reproduce the breakage. Maintainer will write it if you don't.
