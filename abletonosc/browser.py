"""
Custom AbletonOSC handler: browser / preset loading.

Adds handlers to search Live's browser and load an item onto a specific track,
so external clients (atris-studio) can load instruments without UI drag-drop.

Commands:
    /live/browser/load_by_query [track_index, query]
        Walk the browser tree for the first loadable item whose name contains
        `query` (case-insensitive substring). Select track_index, load it.
        Replies on /live/browser/load_by_query with (track_index, query, loaded_name)
        on success, or (track_index, query, "") if no match.

    /live/browser/load_from_category [track_index, category, query]
        Same, but restricted to a top-level browser root:
        category ∈ {sounds, instruments, drums, audio_effects, midi_effects,
                    samples, plugins, clips, user_library, current_project, packs,
                    max_for_live}
        Safer than load_by_query — avoids accidental matches.

    /live/browser/list_categories
        Returns the list of top-level browser roots available.

    /live/browser/list_children [category, depth=1]
        Returns names of children (one level) under the given category — useful
        for discovery before loading.
"""

from __future__ import annotations

import Live

from .handler import AbletonOSCHandler


MAX_DEPTH = 6
MAX_ITEMS_SCANNED = 2000  # safety cap so a bad query doesn't walk 100k presets


CATEGORY_MAP = {
    "sounds": "sounds",
    "instruments": "instruments",
    "drums": "drums",
    "audio_effects": "audio_effects",
    "midi_effects": "midi_effects",
    "samples": "samples",
    "plugins": "plugins",
    "clips": "clips",
    "user_library": "user_library",
    "current_project": "current_project",
    "packs": "packs",
    "max_for_live": "max_for_live",
}


def _safe_name(item) -> str:
    try:
        return item.name or ""
    except Exception:
        return ""


def _safe_is_loadable(item) -> bool:
    try:
        return bool(item.is_loadable)
    except Exception:
        return False


def _safe_children(item):
    try:
        return list(item.iter_children)
    except Exception:
        try:
            return list(item.children)
        except Exception:
            return []


def _find_first_loadable(root, query_lower: str, logger=None):
    """Breadth-first search for a loadable item whose name contains query."""
    queue = [(root, 0)]
    scanned = 0
    while queue and scanned < MAX_ITEMS_SCANNED:
        node, depth = queue.pop(0)
        scanned += 1
        if depth > MAX_DEPTH:
            continue
        name = _safe_name(node).lower()
        if _safe_is_loadable(node) and query_lower in name:
            if logger:
                logger.info("browser: matched '%s' at depth %d (scanned %d)" % (_safe_name(node), depth, scanned))
            return node
        for child in _safe_children(node):
            queue.append((child, depth + 1))
    if logger:
        logger.info("browser: no match for '%s' (scanned %d items)" % (query_lower, scanned))
    return None


class BrowserHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"

    def init_api(self):
        app = Live.Application.get_application()

        def _get_browser():
            return Live.Application.get_application().browser

        def _get_song():
            return Live.Application.get_application().get_document()

        def _select_track(track_index: int) -> bool:
            song = _get_song()
            if track_index < 0 or track_index >= len(song.tracks):
                self.logger.warning("browser: track_index %d out of range (have %d tracks)" % (track_index, len(song.tracks)))
                return False
            song.view.selected_track = song.tracks[track_index]
            return True

        def _resolve_category(name: str):
            browser = _get_browser()
            key = CATEGORY_MAP.get(name.lower())
            if key is None:
                return None
            return getattr(browser, key, None)

        #--------------------------------------------------------------------------------
        # /live/browser/list_categories
        #--------------------------------------------------------------------------------
        def list_categories(_params):
            browser = _get_browser()
            out = []
            for key in CATEGORY_MAP:
                root = getattr(browser, key, None)
                if root is not None:
                    out.append(key)
            self.osc_server.send("/live/browser/list_categories", tuple(out))
        self.osc_server.add_handler("/live/browser/list_categories", list_categories)

        #--------------------------------------------------------------------------------
        # /live/browser/list_children [category, (optional) max_items=30]
        #--------------------------------------------------------------------------------
        def list_children(params):
            category = str(params[0])
            max_items = int(params[1]) if len(params) > 1 else 30
            root = _resolve_category(category)
            if root is None:
                self.osc_server.send("/live/browser/list_children", (category, "error:unknown_category"))
                return
            names = []
            for child in _safe_children(root):
                n = _safe_name(child)
                if n:
                    names.append(n)
                if len(names) >= max_items:
                    break
            self.osc_server.send("/live/browser/list_children", (category, *names))
        self.osc_server.add_handler("/live/browser/list_children", list_children)

        #--------------------------------------------------------------------------------
        # /live/browser/load_by_query [track_index, query]
        #--------------------------------------------------------------------------------
        def load_by_query(params):
            track_index = int(params[0])
            query = str(params[1])
            query_lower = query.lower()

            if not _select_track(track_index):
                self.osc_server.send("/live/browser/load_by_query", (track_index, query, ""))
                return

            browser = _get_browser()
            # scan the main user-facing roots in priority order
            for key in ("sounds", "instruments", "drums", "samples", "packs", "user_library"):
                root = getattr(browser, key, None)
                if root is None:
                    continue
                item = _find_first_loadable(root, query_lower, logger=self.logger)
                if item is not None:
                    try:
                        browser.load_item(item)
                    except Exception as e:
                        self.logger.warning("browser: load_item raised %s for %s" % (e, _safe_name(item)))
                        continue
                    self.osc_server.send("/live/browser/load_by_query", (track_index, query, _safe_name(item)))
                    return
            self.osc_server.send("/live/browser/load_by_query", (track_index, query, ""))
        self.osc_server.add_handler("/live/browser/load_by_query", load_by_query)

        #--------------------------------------------------------------------------------
        # /live/browser/load_from_category [track_index, category, query]
        #--------------------------------------------------------------------------------
        def load_from_category(params):
            track_index = int(params[0])
            category = str(params[1])
            query = str(params[2])
            query_lower = query.lower()

            if not _select_track(track_index):
                self.osc_server.send("/live/browser/load_from_category", (track_index, category, query, ""))
                return

            root = _resolve_category(category)
            if root is None:
                self.osc_server.send("/live/browser/load_from_category", (track_index, category, query, "error:unknown_category"))
                return

            item = _find_first_loadable(root, query_lower, logger=self.logger)
            if item is None:
                self.osc_server.send("/live/browser/load_from_category", (track_index, category, query, ""))
                return

            browser = _get_browser()
            try:
                browser.load_item(item)
            except Exception as e:
                self.logger.warning("browser: load_item raised %s for %s" % (e, _safe_name(item)))
                self.osc_server.send("/live/browser/load_from_category", (track_index, category, query, "error:load_failed"))
                return

            self.osc_server.send("/live/browser/load_from_category", (track_index, category, query, _safe_name(item)))
        self.osc_server.add_handler("/live/browser/load_from_category", load_from_category)
