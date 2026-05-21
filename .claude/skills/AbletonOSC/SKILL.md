---
name: AbletonOSC
description: Development skill for ideoforms/AbletonOSC — Python remote-script that exposes Ableton Live to OSC. How to add endpoints the maintainer will actually merge, and how to avoid the stale-fork trap.
domain: repository-specific
version: 1.0.0
generated: 2026-05-21
source_repo: https://github.com/ideoforms/AbletonOSC
source_platform: github
tags: [python, ableton, osc, remote-script, midi]
triggers:
  keywords:
    primary: [abletonosc, ableton-osc, ideoforms]
    secondary: [osc, ableton, live, remote-script, /live/]
---

# AbletonOSC Development Skill

> Auto-generated 2026-05-21. Re-run `/github-cloner https://github.com/ideoforms/AbletonOSC` to refresh.

## Repository Overview

**ideoforms/AbletonOSC** — Control Ableton Live via Open Sound Control (OSC). Python remote-script that runs inside Live and exposes the Live API over an OSC server. Single maintainer, 743 stars, MIT.

## Project Structure

```
AbletonOSC/
├── abletonosc/             # Remote-script package (loaded by Live)
│   ├── __init__.py
│   ├── handler.py          # AbletonOSCHandler base — generic get/set/listen plumbing
│   ├── osc_server.py
│   ├── application.py      # /live/application/*
│   ├── song.py             # /live/song/*
│   ├── track.py            # /live/track/*
│   ├── clip.py             # /live/clip/*
│   ├── clip_slot.py        # /live/clip_slot/*
│   ├── scene.py            # /live/scene/*
│   ├── view.py             # /live/view/*
│   ├── device.py           # /live/device/*
│   ├── midimap.py
│   ├── introspection.py
│   └── constants.py
├── tests/                  # pytest, runs against a LIVE Ableton instance
│   ├── __init__.py         # AbletonOSCClient fixture, TICK_DURATION=0.125
│   ├── test_application.py
│   ├── test_bundle.py
│   ├── test_clip.py
│   ├── test_clip_slot.py
│   ├── test_song.py
│   ├── test_track.py
│   └── test_view.py
├── client/                 # Python OSC client library (used by tests + run-console)
├── pythonosc/              # Vendored python-osc
├── run-console.py          # Interactive REPL with tab-autocomplete
├── manager.py
├── README.md               # ~66KB — every endpoint is documented in big tables
└── CONTRIBUTING.md
```

## The Core Pattern — Adding an Endpoint

Endpoints come for free if the underlying `Live.<Object>` has a matching attribute. The handler base class wires them.

`abletonosc/handler.py::AbletonOSCHandler` provides generic plumbing:
- `_get_property(target, prop, params)` — reads attribute, gracefully returns `None` on `RuntimeError`
- `_set_property(target, prop, params)` — `setattr`
- `_call_method(target, method, params)` — `getattr(...)(*params)`
- `_start_listen` / `_stop_listen` — wraps Live's `add_<prop>_listener` / `remove_<prop>_listener`

Each module's `init_api()` declares three lists. The framework auto-registers `/live/<class>/get/<prop>`, `/live/<class>/set/<prop>`, `/live/<class>/start_listen/<prop>`, `/live/<class>/stop_listen/<prop>`:

```python
methods       = ["fire", "stop", ...]                  # → /live/clip/fire
properties_r  = ["is_playing", "length", ...]          # → get + listen
properties_rw = ["name", "color", "warp_mode", ...]    # → get + set + listen
```

**To add a new Live property as an endpoint**: append the property name to `properties_r` or `properties_rw`. README table entry + (optionally) a test. That's it. PR #143 added 14 clip properties this way — three files changed, no tests, merged.

For anything that returns a non-primitive (`groove`, `view`, `warp_markers`), the generic getter throws `"Infered arg_value type is not supported"` and needs a custom handler — leave it commented out with that note (see `clip.py` TODO block).

## How Tests Work

`pytest` runs against a **running Ableton Live instance** (not a mock). CONTRIBUTING.md preconditions:
- Live started with blank default set
- Default audio input + output configured
- Preferences > Record, Warp & Launch > Count-In = None

`tests/__init__.py` boots an `AbletonOSCClient` fixture (module-scoped) and sends `/live/api/reload` on import so the test pass picks up code changes. Each test:

```python
def _test_clip_property(client, track_id, clip_id, property, values):
    for value in values:
        client.send_message("/live/clip/set/%s" % property, (track_id, clip_id, value))
        wait_one_tick()
        assert client.query("/live/clip/get/%s" % property, (track_id, clip_id)) == (track_id, clip_id, value,)
```

Two-step setup: `_create_test_clips` fixture creates an empty MIDI clip on track 0 + arms track 2 and records a brief audio clip. Tests then set/query/round-trip. `wait_one_tick()` = `time.sleep(0.125)` between mutations and assertions.

`test_clip_listen_lifecycle` is the template for listener tests: `start_listen` → mutate → `await_message` → mutate again → `stop_listen`.

## Maintainer Preferences (Daniel Jones, @ideoforms)

Quotes from actual reviews:

- **Lean codebase**: *"I want to keep the codebase as lean and simple as possible, as extra code and files creates a long-term maintenance burden."* (PR #167 review)
- **No surplus docs/files**: *"Please remove all of the new markdown files, and all of the files in `devel`."* (PR #167)
- **Reuse existing namespaces**: *"API-wise, I think this fits neatly under the existing /live/view namespace - /live/view/scroll_view would be a good location."* (PR #153)
- **Skeptical of AI-bloat PRs**: PR template literally says *"long PRs containing a lot of AI-generated content are complex and time-consuming to review."*
- **Pragmatic on tests**: PR #143 (clip property additions) merged with no tests. Tests are *required* for new logic/methods, *encouraged* for new properties, *not blocking* for trivial list-additions.

What gets merged fast:
- Small focused PRs (≤200 lines, 1-3 files)
- Property list additions (PR #143 = 100/-32, 3 files, merged in days)
- Bug fixes with a unit test that demonstrates the bug (PR #89 was held until the test was extended)

What stalls:
- Massive refactors (PR #185 = 1734/-363; PR #186 = 1135/-321) — sit open for months
- Multiple competing implementations of the same area (5 open Browser API PRs: #183, #191, #192, #194, #200)
- New top-level concepts without an existing namespace (PR #170 chain stuff)
- PRs that delete maintainer's structure (issue templates, etc.)

## Common Pitfalls

| Pitfall | Fix | Seen in |
|---------|-----|---------|
| Stale fork — branched before `git pull` of upstream | `git fetch origin && git diff origin/master` before opening any PR. Confirm no overlap with recently merged PRs. | PR #201 (closed — duplicated already-merged PR #143) |
| Non-primitive property return crashes generic getter | Write a custom handler instead of adding to `properties_r`, or leave commented with the "Infered arg_value type is not supported" note | `clip.py` groove/view/warp_markers TODOs |
| New endpoint placed in own namespace when an existing one fits | Check `/live/view/`, `/live/song/`, `/live/track/` first. Reuse. | PR #153 (asked to move from `/live/application/view/` to `/live/view/`) |
| Big PR with `devel/`, extra markdown, AI-generated commentary | Strip to the minimum delta. Maintainer will ask for removal. | PR #167 |
| Multiple competing implementations of same area open simultaneously | Check open PRs in target area before starting. Coordinate or pick up an existing one. | Browser API: #183 #191 #192 #194 #200 |

## Finishing Esa's Open PRs

PR #201 (the only one currently open from @esaruoho) was a stale-fork duplicate of merged #143 and has been closed.

If a future Esa PR is asked for tests, the recipe is:

1. Open Live with a blank set + default I/O + Count-In = None
2. `pip3 install pytest`
3. `cd ~/work/AbletonOSC`
4. Add a test next to a sibling in the right `tests/test_<module>.py`:
   - **Property round-trip**: `_test_<module>_property(client, ids..., "prop", (val1, val2))` — mirrors `test_clip_property_name`
   - **Method**: `client.send_message(...)` then `client.query(...)` to assert state. Mirror `test_clip_add_remove_notes`.
   - **Listener**: `start_listen` → `send_message` → `await_message(..., TICK_DURATION * 2)` → `stop_listen`. Mirror `test_clip_listen_lifecycle`.
5. `pytest tests/test_<module>.py::test_<name>` to run just that test
6. If a property returns a non-primitive (tuple, object), do NOT add to `properties_r` — write a dedicated handler that returns primitives

## Key Contributors

| Contributor | Handle | Commits | Focus Areas |
|-------------|--------|---------|-------------|
| Daniel Jones | @ideoforms | 251 | Maintainer — everything |
| Mark Marijnissen | @markmarijnissen | 11 | view.py, master/return tracks |
| Esa Juhani Ruoho | @esaruoho | 8 | Clip property additions, run-console autocomplete |
| Marco Buongiorno Nardelli | @marcobn | 7 | — |
| Dave Bailey | @steeltrack | 6 | Send/return improvements |

Notable contributors in open PRs:
- Garrison Burger (@PhotonicVelocity) — large refactor PRs #182/#185/#186 (dictionary-registry pattern, stalled)
- Zach Bimson (@bimsonz) — multiple feature PRs (#195-#199)
- Thomas Couderc (@elzinko) — #167 Device Variations API for Live 12
- Keshav Rao (@keshav55) — #200 browser handlers

## Quick Reference

| Item | Value |
|------|-------|
| Source Platform | GitHub |
| Primary Language | Python |
| Default Branch | master |
| License | MIT |
| Maintainer | @ideoforms (Daniel Jones) |
| Open Issues | 38 |
| Open PRs | 23 |
| Merged PRs | 20 |
| Forks | 136 |
| Working clone | `~/work/AbletonOSC/` |
| Last Analyzed | 2026-05-21 |

## Reload Without Restarting Live

Send `/live/reload` (or `/live/api/reload`) over OSC. The handler modules reimport. Tests do this on module import.

## Live Boot Log (for debugging compile errors)

```bash
LOG_DIR="$HOME/Library/Application Support/Ableton/Live Reports/Usage"
LOG_FILE=$(ls -atr "$LOG_DIR"/*.log | tail -1)
tail -5000f "$LOG_FILE" | grep AbletonOSC
```

Runtime log: `logs/abletonosc.log` relative to the AbletonOSC directory.
