"""
Browser handler — load instruments, effects, and presets onto tracks via the Live Browser API.

Endpoints:
    /live/browser/load_preset  (track_index: int, path: str)
        Walk the User Library browser tree to find the preset at the given
        relative path (e.g. "Presets/Instruments/Drum Rack/MyKit.adg"),
        select the target track, and load the preset onto it.

    /live/browser/load_effect  (track_index: int, effect_name: str)
        Load any Ableton audio/MIDI effect by name onto a track.
        Searches built-in effects categories. Examples:
            ("Compressor", "Reverb", "Delay", "Drum Buss", "EQ Eight",
             "Glue Compressor", "Saturator", "Echo", "Corpus", "Roar")

    /live/browser/list_items  (category: str, path: str)
        List items in a browser category. Returns names of children.
        Categories: user_library, instruments, drums, sounds, audio_effects,
                    midi_effects, packs, samples, plugins, max_for_live

    /live/browser/refresh  ()
        Force Ableton to rescan the User Library browser tree.
        Call this after generating new presets before loading them.
"""

import Live
from .handler import AbletonOSCHandler


class BrowserHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"

    def init_api(self):
        self.osc_server.add_handler("/live/browser/load_preset", self._load_preset)
        self.osc_server.add_handler("/live/browser/load_effect", self._load_effect)
        self.osc_server.add_handler("/live/browser/load_instrument", self._load_instrument)
        self.osc_server.add_handler("/live/browser/list_items", self._list_items)
        self.osc_server.add_handler("/live/browser/refresh", self._refresh)

    def _get_browser(self):
        return self.manager.application.browser

    def _walk_path(self, root_item, path_parts):
        """Walk the browser tree following the given path segments.

        Returns the BrowserItem at the end of the path, or None.
        """
        current = root_item
        for part in path_parts:
            found = False
            for child in current.children:
                if child.name == part:
                    current = child
                    found = True
                    break
            if not found:
                # Try case-insensitive match
                for child in current.children:
                    if child.name.lower() == part.lower():
                        current = child
                        found = True
                        break
            if not found:
                # Try matching without extension
                part_no_ext = part.rsplit(".", 1)[0] if "." in part else part
                for child in current.children:
                    child_no_ext = child.name.rsplit(".", 1)[0] if "." in child.name else child.name
                    if child_no_ext.lower() == part_no_ext.lower():
                        current = child
                        found = True
                        break
            if not found:
                self.logger.warning("Browser path segment not found: '%s' (available: %s)" %
                                    (part, ", ".join(c.name for c in current.children)))
                return None
        return current

    def _find_in_category(self, browser, category, preset_name):
        """Search a browser category for a preset by name.

        Walks one or two levels deep looking for a matching item.
        Returns the BrowserItem if found, else None.
        """
        root = getattr(browser, category, None)
        if root is None:
            return None

        # Strip .adg for comparison
        name_no_ext = preset_name.rsplit(".", 1)[0] if "." in preset_name else preset_name

        def match(child):
            child_no_ext = child.name.rsplit(".", 1)[0] if "." in child.name else child.name
            return child_no_ext.lower() == name_no_ext.lower()

        # Check direct children
        for child in root.children:
            if match(child):
                self.logger.info("Found '%s' in browser.%s (direct)" %
                                 (child.name, category))
                return child

        # Check one level deeper (e.g. Drum Rack subfolder)
        for child in root.children:
            try:
                for grandchild in child.children:
                    if match(grandchild):
                        self.logger.info("Found '%s' in browser.%s/%s" %
                                         (grandchild.name, category, child.name))
                        return grandchild
            except Exception:
                continue

        return None

    def _refresh(self, params):
        """Force Ableton to rescan the browser by toggling filter type.

        This nudges Ableton into re-reading the file system for any
        browser categories that are accessed afterward.
        """
        browser = self._get_browser()
        try:
            # Toggling the filter_type forces Ableton to invalidate
            # its cached browser tree and rescan on next access.
            original = browser.filter_type
            # Cycle to a different filter and back
            if original != Live.Browser.FilterType.disabled:
                browser.filter_type = Live.Browser.FilterType.disabled
            else:
                browser.filter_type = Live.Browser.FilterType.instrument_rack
            browser.filter_type = original
            self.logger.info("Browser refresh: toggled filter_type")
            return ("ok", "refreshed")
        except Exception as e:
            self.logger.warning("Browser filter toggle failed: %s — "
                                "trying hotswap fallback" % e)

        # Fallback: just log available categories for diagnostics
        try:
            cats = []
            for attr in ("user_library", "drums", "instruments", "sounds",
                         "audio_effects", "midi_effects", "packs"):
                root = getattr(browser, attr, None)
                if root is not None:
                    count = sum(1 for _ in root.children)
                    cats.append("%s(%d)" % (attr, count))
            self.logger.info("Browser categories: %s" % ", ".join(cats))
            return ("ok", "categories logged")
        except Exception as e2:
            self.logger.error("Browser refresh failed: %s" % e2)
            return ("error", str(e2))

    def _load_preset(self, params):
        """Load a preset onto a track.

        Args:
            params[0]: track_index (int) — which track to load onto
            params[1]: path (str) — relative path within User Library,
                       e.g. "Presets/Instruments/Drum Rack/MyKit.adg"
                       OR just the preset name, e.g. "MyKit" or "MyKit.adg"
        """
        if len(params) < 2:
            self.logger.error("load_preset requires (track_index, path)")
            return ("error", "requires track_index and path")

        track_index = int(params[0])
        preset_path = str(params[1])

        browser = self._get_browser()
        song = self.song

        # Select the target track
        if track_index < 0 or track_index >= len(song.tracks):
            self.logger.error("Track index %d out of range" % track_index)
            return ("error", "track index out of range")

        song.view.selected_track = song.tracks[track_index]

        # Parse the path into segments
        path_parts = [p for p in preset_path.replace("\\", "/").split("/") if p]

        # If just a name (no path separators), search in Drum Rack presets
        if len(path_parts) == 1:
            path_parts = ["Presets", "Instruments", "Drum Rack", path_parts[0]]

        # Walk the user library tree
        root = browser.user_library
        item = self._walk_path(root, path_parts)

        # Fallback: if user_library root is stale (common after reload
        # or when new files were added), try the category-based browser
        # roots which Ableton keeps fresh.
        if item is None and path_parts[:3] == ["Presets", "Instruments", "Drum Rack"]:
            preset_name = path_parts[-1]
            self.logger.info("Trying browser.drums fallback for '%s'" % preset_name)
            item = self._find_in_category(browser, "drums", preset_name)
            if item is None:
                self.logger.info("Trying browser.instruments fallback for '%s'" % preset_name)
                item = self._find_in_category(browser, "instruments", preset_name)

        if item is None:
            self.logger.error("Preset not found: %s" % preset_path)
            return ("error", "preset not found: %s" % preset_path)

        if not item.is_loadable:
            self.logger.error("Item is not loadable: %s" % item.name)
            return ("error", "item not loadable: %s" % item.name)

        # Load it!
        browser.load_item(item)
        self.logger.info("Loaded preset '%s' onto track %d" % (item.name, track_index))
        self.manager.show_message("Loaded: %s" % item.name)

        return (track_index, item.name)

    def _load_effect(self, params):
        """Load an audio or MIDI effect onto a track by name.

        Searches Ableton's built-in effects browser categories to find
        the effect, then loads it onto the selected track. Works with
        any stock Ableton effect: Compressor, Reverb, Delay, Drum Buss,
        Glue Compressor, EQ Eight, Saturator, etc.

        Args:
            params[0]: track_index (int) — which track to load onto
            params[1]: effect_name (str) — name of the effect, e.g.
                       "Compressor", "Reverb", "Drum Buss", "EQ Eight"
        """
        if len(params) < 2:
            self.logger.error("load_effect requires (track_index, effect_name)")
            return ("error", "requires track_index and effect_name")

        track_index = int(params[0])
        effect_name = str(params[1])

        browser = self._get_browser()
        song = self.song

        # Select the target track
        if track_index < 0 or track_index >= len(song.tracks):
            self.logger.error("Track index %d out of range" % track_index)
            return ("error", "track index out of range")

        song.view.selected_track = song.tracks[track_index]

        # Search audio_effects first (most common), then midi_effects
        item = self._find_in_category(browser, "audio_effects", effect_name)
        if item is None:
            item = self._find_in_category(browser, "midi_effects", effect_name)

        # Also try searching deeper — some effects are in subcategories
        if item is None:
            item = self._deep_search(browser, "audio_effects", effect_name)
        if item is None:
            item = self._deep_search(browser, "midi_effects", effect_name)

        if item is None:
            self.logger.error("Effect not found: %s" % effect_name)
            return ("error", "effect not found: %s" % effect_name)

        if not item.is_loadable:
            self.logger.error("Effect is not loadable: %s" % item.name)
            return ("error", "effect not loadable: %s" % item.name)

        # Load it!
        browser.load_item(item)
        self.logger.info("Loaded effect '%s' onto track %d" % (item.name, track_index))
        self.manager.show_message("Effect: %s" % item.name)

        return (track_index, item.name)

    def _load_instrument(self, params):
        """Load an instrument onto a track by name.

        Searches Ableton's built-in instruments browser category.
        Works with: Analog, Collision, Drift, Meld, Operator, Simpler,
        Sampler, Tension, Wavetable, etc.

        Args:
            params[0]: track_index (int) — which track to load onto
            params[1]: instrument_name (str) — e.g. "Meld", "Operator"
        """
        if len(params) < 2:
            self.logger.error("load_instrument requires (track_index, instrument_name)")
            return ("error", "requires track_index and instrument_name")

        track_index = int(params[0])
        instrument_name = str(params[1])

        browser = self._get_browser()
        song = self.song

        if track_index < 0 or track_index >= len(song.tracks):
            self.logger.error("Track index %d out of range" % track_index)
            return ("error", "track index out of range")

        song.view.selected_track = song.tracks[track_index]

        # Search instruments category
        item = self._find_in_category(browser, "instruments", instrument_name)
        if item is None:
            item = self._deep_search(browser, "instruments", instrument_name)
        # Also try sounds (some instruments live there)
        if item is None:
            item = self._find_in_category(browser, "sounds", instrument_name)
        if item is None:
            item = self._deep_search(browser, "sounds", instrument_name)

        if item is None:
            self.logger.error("Instrument not found: %s" % instrument_name)
            return ("error", "instrument not found: %s" % instrument_name)

        if not item.is_loadable:
            self.logger.error("Instrument is not loadable: %s" % item.name)
            return ("error", "instrument not loadable: %s" % item.name)

        browser.load_item(item)
        self.logger.info("Loaded instrument '%s' onto track %d" % (item.name, track_index))
        self.manager.show_message("Instrument: %s" % item.name)

        return (track_index, item.name)

    def _deep_search(self, browser, category, name):
        """Search up to 3 levels deep in a browser category for an item.

        Ableton organizes effects into subcategories (Audio Effects ->
        Dynamics -> Compressor, Audio Effects -> Delay -> Echo, etc.)
        """
        root = getattr(browser, category, None)
        if root is None:
            return None

        name_lower = name.lower()

        def match(item):
            item_name = item.name.rsplit(".", 1)[0] if "." in item.name else item.name
            return item_name.lower() == name_lower

        # Level 1 (direct children)
        for child in root.children:
            if match(child):
                return child

        # Level 2 (subcategories like "Dynamics", "Delay", "Distortion")
        for child in root.children:
            try:
                for grandchild in child.children:
                    if match(grandchild):
                        self.logger.info("Found '%s' in %s/%s" %
                                         (grandchild.name, category, child.name))
                        return grandchild
            except Exception:
                continue

        # Level 3 (presets inside effect folders)
        for child in root.children:
            try:
                for grandchild in child.children:
                    try:
                        for great in grandchild.children:
                            if match(great):
                                self.logger.info("Found '%s' in %s/%s/%s" %
                                                 (great.name, category, child.name, grandchild.name))
                                return great
                    except Exception:
                        continue
            except Exception:
                continue

        return None

    def _list_items(self, params):
        """List children of a browser category/path.

        Args:
            params[0]: category (str) — e.g. "user_library", "instruments", "drums"
            params[1]: path (str, optional) — sub-path to list, "/" separated
        """
        if len(params) < 1:
            return ("error", "requires category name")

        category = str(params[0])
        sub_path = str(params[1]) if len(params) > 1 else ""

        browser = self._get_browser()

        # Get the root category
        root = getattr(browser, category, None)
        if root is None:
            available = [attr for attr in dir(browser) if not attr.startswith("_")
                         and hasattr(getattr(browser, attr), "children")]
            self.logger.error("Unknown category: %s (available: %s)" %
                              (category, ", ".join(available)))
            return ("error", "unknown category")

        # Walk sub-path if provided
        if sub_path:
            path_parts = [p for p in sub_path.replace("\\", "/").split("/") if p]
            target = self._walk_path(root, path_parts)
            if target is None:
                return ("error", "path not found")
        else:
            target = root

        # Return child names
        children = tuple(child.name for child in target.children)
        return children
