from typing import Tuple, Any, List
from .handler import AbletonOSCHandler
import Live
import logging

logger = logging.getLogger("abletonosc")


class BrowserHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"

    @property
    def browser(self):
        return Live.Application.get_application().browser

    # ---- Core helpers ----

    def _get_category(self, category_name):
        """Map a category string to a browser root item."""
        attr_map = {
            "instruments": "instruments",
            "drums": "drums",
            "audio_effects": "audio_effects",
            "midi_effects": "midi_effects",
            "sounds": "sounds",
            "packs": "packs",
            "samples": "samples",
            "clips": "clips",
            "max_for_live": "max_for_live",
            "plugins": "plugins",
            "user_library": "user_library",
        }

        attr_name = attr_map.get(category_name.lower())
        if attr_name:
            try:
                return getattr(self.browser, attr_name)
            except (AttributeError, RuntimeError):
                pass

        try:
            for folder in self.browser.user_folders:
                if folder.name.lower() == category_name.lower():
                    return folder
        except Exception:
            pass

        return None

    def _match_name(self, child_name, search_name):
        """
        Compare names with tiered matching.
        Returns: 3=exact/case-insensitive, 2=extension-stripped, 1=substring, 0=no match.
        """
        child_lower = child_name.lower()
        search_lower = search_name.lower()
        if child_lower == search_lower:
            return 3
        child_bare = child_name.rsplit(".", 1)[0].lower() if "." in child_name else child_lower
        if child_bare == search_lower:
            return 2
        if search_lower in child_bare:
            return 1
        return 0

    def _find_item(self, parent, name, max_depth=4, current_depth=0):
        """
        Search browser tree for an item by name.
        Priority: exact/case-insensitive > extension-stripped > substring.
        Returns first loadable match at highest priority, or None.
        """
        if current_depth > max_depth:
            return None
        try:
            children = list(parent.children)
        except Exception:
            return None

        substring_match = None
        folders_to_search = []

        for child in children:
            try:
                child_name = child.name
            except Exception:
                continue

            quality = self._match_name(child_name, name)

            if quality >= 2:
                if child.is_loadable:
                    return child
                if child.is_folder:
                    result = self._find_item(child, name, max_depth, current_depth + 1)
                    if result:
                        return result
            elif quality == 1 and child.is_loadable and not substring_match:
                substring_match = child

            if child.is_folder and quality < 2:
                folders_to_search.append(child)

        for folder in folders_to_search:
            result = self._find_item(folder, name, max_depth, current_depth + 1)
            if result:
                return result

        return substring_match

    def _search_items(self, parent, query, results, max_results=20, max_depth=3, current_depth=0):
        """Collect loadable items whose name contains the query string."""
        if current_depth > max_depth or len(results) >= max_results:
            return
        try:
            children = list(parent.children)
        except Exception:
            return
        for child in children:
            if len(results) >= max_results:
                return
            try:
                child_name = child.name
            except Exception:
                continue
            if query.lower() in child_name.lower() and child.is_loadable:
                results.append(child_name)
            if child.is_folder and current_depth < max_depth:
                self._search_items(child, query, results, max_results, max_depth, current_depth + 1)

    def _collect_loadable(self, parent, results, max_results=100, max_depth=2, current_depth=0):
        """Collect all loadable item names from a browser tree."""
        if current_depth > max_depth or len(results) >= max_results:
            return
        try:
            children = list(parent.children)
        except Exception:
            return
        for child in children:
            if len(results) >= max_results:
                return
            try:
                if child.is_loadable:
                    results.append(child.name)
                elif child.is_folder and current_depth < max_depth:
                    self._collect_loadable(child, results, max_results, max_depth, current_depth + 1)
            except Exception:
                continue

    def _get_children_info(self, parent):
        """Get flattened (name, is_loadable, is_folder, ...) for immediate children."""
        result = []
        try:
            for child in parent.children:
                try:
                    result.append(child.name)
                    result.append(1 if child.is_loadable else 0)
                    result.append(1 if child.is_folder else 0)
                except Exception:
                    continue
        except Exception:
            pass
        return tuple(result)

    def _navigate_path(self, parent, path_parts):
        """Navigate browser tree by path segments with fallback matching."""
        current = parent
        for part in path_parts:
            found = None
            try:
                for child in current.children:
                    if self._match_name(child.name, part) >= 2:
                        found = child
                        break
            except Exception:
                return None
            if not found:
                return None
            current = found
        return current

    def _select_track(self, track_index):
        """Select a track by index and return it."""
        track = self.song.tracks[track_index]
        self.song.view.selected_track = track
        return track

    def _load_from_categories(self, name, track_index, category_names):
        """Search for and load an item by name across multiple categories."""
        self._select_track(track_index)

        for cat_name in category_names:
            category = self._get_category(cat_name)
            if category:
                item = self._find_item(category, name)
                if item:
                    self.browser.load_item(item)
                    logger.info("Loaded '%s' from %s onto track %d" % (item.name, cat_name, track_index))
                    return (item.name,)

        raise ValueError("Not found: %s (searched: %s)" % (name, ", ".join(category_names)))

    def _refresh(self):
        """Force browser cache invalidation by toggling filter_type."""
        try:
            original = self.browser.filter_type
            try:
                self.browser.filter_type = Live.Browser.FilterType.disabled_filter_type
            except Exception:
                self.browser.filter_type = 0 if original != 0 else 1
            self.browser.filter_type = original
            logger.info("Browser cache refreshed")
        except Exception as e:
            logger.warning("Browser refresh failed: %s" % e)

    # ---- API registration ----

    def init_api(self):

        # ---- Load by name (10 endpoints) ----

        def load_instrument(params: Tuple[Any]):
            """/live/browser/load_instrument (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["instruments", "drums", "sounds"])

        def load_drum_kit(params: Tuple[Any]):
            """/live/browser/load_drum_kit (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["drums"])

        def load_audio_effect(params: Tuple[Any]):
            """/live/browser/load_audio_effect (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["audio_effects"])

        def load_midi_effect(params: Tuple[Any]):
            """/live/browser/load_midi_effect (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["midi_effects"])

        def load_effect(params: Tuple[Any]):
            """/live/browser/load_effect (name, track_index) — searches both audio and MIDI effects"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["audio_effects", "midi_effects"])

        def load_sound(params: Tuple[Any]):
            """/live/browser/load_sound (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["sounds"])

        def load_sample(params: Tuple[Any]):
            """/live/browser/load_sample (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["samples"])

        def load_plugin(params: Tuple[Any]):
            """/live/browser/load_plugin (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["plugins", "instruments", "audio_effects"])

        def load_max_device(params: Tuple[Any]):
            """/live/browser/load_max_device (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["max_for_live"])

        def load_user_preset(params: Tuple[Any]):
            """/live/browser/load_user_preset (name, track_index)"""
            name, track_index = str(params[0]), int(params[1])
            return self._load_from_categories(name, track_index, ["user_library"])

        # ---- Load by target (2 endpoints) ----

        def load_to_slot(params: Tuple[Any]):
            """Load item into a specific session clip slot.
            /live/browser/load_to_slot (category, name, track_index, slot_index)
            Uses highlighted_clip_slot to target the exact slot.
            """
            category_name = str(params[0])
            name = str(params[1])
            track_index = int(params[2])
            slot_index = int(params[3])

            category = self._get_category(category_name)
            if not category:
                raise ValueError("Category not found: %s" % category_name)

            item = self._find_item(category, name)
            if not item:
                raise ValueError("Not found in %s: %s" % (category_name, name))

            app = Live.Application.get_application()
            track = self.song.tracks[track_index]
            scene = self.song.scenes[slot_index]
            clip_slot = track.clip_slots[slot_index]

            try:
                app.view.show_view("Session")
                app.view.focus_view("Session")
            except Exception:
                pass

            self.song.view.selected_track = track
            self.song.view.selected_scene = scene
            self.song.view.highlighted_clip_slot = clip_slot

            self.browser.load_item(item)
            logger.info("Loaded '%s' to slot (track %d, slot %d)" % (item.name, track_index, slot_index))
            return (item.name, track_index, slot_index)

        def load_to_arrangement(params: Tuple[Any]):
            """Load item at a position in arrangement view.
            /live/browser/load_to_arrangement (category, name, track_index, beat_time)
            Note: arrangement targeting is best-effort as the Live API
            does not support direct positional insertion.
            """
            category_name = str(params[0])
            name = str(params[1])
            track_index = int(params[2])
            beat_time = float(params[3])

            category = self._get_category(category_name)
            if not category:
                raise ValueError("Category not found: %s" % category_name)

            item = self._find_item(category, name)
            if not item:
                raise ValueError("Not found in %s: %s" % (category_name, name))

            app = Live.Application.get_application()
            track = self.song.tracks[track_index]

            try:
                app.view.show_view("Arranger")
                app.view.focus_view("Arranger")
            except Exception:
                pass

            self.song.view.selected_track = track
            self.song.current_song_time = beat_time

            self.browser.load_item(item)
            logger.info("Loaded '%s' to arrangement (track %d, beat %.1f)" % (item.name, track_index, beat_time))
            return (item.name, track_index, beat_time)

        # ---- Discovery (8 endpoints) ----

        def get_categories(params: Tuple[Any]):
            """/live/browser/get/categories — list available browser categories"""
            categories = []
            for attr_name in ["instruments", "drums", "audio_effects", "midi_effects",
                              "sounds", "packs", "samples", "clips", "max_for_live",
                              "plugins", "user_library"]:
                try:
                    cat = getattr(self.browser, attr_name)
                    if cat:
                        categories.append(attr_name)
                except (AttributeError, RuntimeError):
                    pass
            return tuple(categories)

        def get_children(params: Tuple[Any]):
            """List children of a browser path.
            /live/browser/get/children (category, [path_part1, ...])
            Returns flat tuple of child names.
            """
            category_name = str(params[0])
            path_parts = [str(p) for p in params[1:]] if len(params) > 1 else []

            category = self._get_category(category_name)
            if not category:
                raise ValueError("Category not found: %s" % category_name)

            if path_parts:
                target = self._navigate_path(category, path_parts)
                if not target:
                    raise ValueError("Path not found: %s/%s" % (category_name, "/".join(path_parts)))
            else:
                target = category

            names = []
            try:
                for child in target.children:
                    try:
                        names.append(child.name)
                    except Exception:
                        continue
            except Exception:
                pass
            return tuple(names)

        def search(params: Tuple[Any]):
            """/live/browser/search (query, [max_results])"""
            query = str(params[0])
            max_results = int(params[1]) if len(params) > 1 else 20
            results = []

            for cat_name in ["instruments", "drums", "audio_effects", "midi_effects",
                             "sounds", "samples", "plugins", "max_for_live"]:
                category = self._get_category(cat_name)
                if category:
                    self._search_items(category, query, results, max_results=max_results, max_depth=4)

            return tuple(results)

        def list_audio_effects(params: Tuple[Any]):
            """/live/browser/list_audio_effects"""
            results = []
            category = self._get_category("audio_effects")
            if category:
                self._collect_loadable(category, results)
            return tuple(results)

        def list_midi_effects(params: Tuple[Any]):
            """/live/browser/list_midi_effects"""
            results = []
            category = self._get_category("midi_effects")
            if category:
                self._collect_loadable(category, results)
            return tuple(results)

        def list_sounds(params: Tuple[Any]):
            """/live/browser/list_sounds"""
            results = []
            category = self._get_category("sounds")
            if category:
                self._collect_loadable(category, results)
            return tuple(results)

        def list_plugins(params: Tuple[Any]):
            """/live/browser/list_plugins"""
            results = []
            category = self._get_category("plugins")
            if category:
                self._collect_loadable(category, results)
            return tuple(results)

        def list_user_presets(params: Tuple[Any]):
            """/live/browser/list_user_presets"""
            results = []
            category = self._get_category("user_library")
            if category:
                self._collect_loadable(category, results)
            return tuple(results)

        # ---- Preview (2 endpoints) ----

        def preview(params: Tuple[Any]):
            """/live/browser/preview (category, name)"""
            category_name = str(params[0])
            name = str(params[1])

            category = self._get_category(category_name)
            if not category:
                raise ValueError("Category not found: %s" % category_name)

            item = self._find_item(category, name)
            if not item:
                raise ValueError("Not found in %s: %s" % (category_name, name))

            self.browser.preview_item(item)
            logger.info("Previewing: %s" % item.name)
            return (item.name,)

        def stop_preview(params: Tuple[Any]):
            """/live/browser/stop_preview"""
            self.browser.stop_preview()
            return ("stopped",)

        # ---- Utility (3 endpoints) ----

        def refresh(params: Tuple[Any]):
            """/live/browser/refresh — force browser cache invalidation"""
            self._refresh()
            return ("refreshed",)

        def hotswap_start(params: Tuple[Any]):
            """Enter hotswap mode for a device.
            /live/browser/hotswap_start (track_index, device_index)
            """
            track_index = int(params[0])
            device_index = int(params[1])
            track = self.song.tracks[track_index]
            device = track.devices[device_index]
            self.browser.hotswap_target = device
            logger.info("Hotswap started for device %d on track %d" % (device_index, track_index))
            return (track_index, device_index)

        def hotswap_load(params: Tuple[Any]):
            """Load an item in the current hotswap context.
            /live/browser/hotswap_load (name)
            """
            name = str(params[0])

            for cat_name in ["instruments", "drums", "audio_effects", "midi_effects",
                             "sounds", "plugins", "max_for_live", "user_library"]:
                category = self._get_category(cat_name)
                if category:
                    item = self._find_item(category, name)
                    if item:
                        self.browser.load_item(item)
                        logger.info("Hotswap loaded: %s" % item.name)
                        return (item.name,)

            raise ValueError("Not found for hotswap: %s" % name)

        # ---- Register all handlers ----

        # Load by name
        self.osc_server.add_handler("/live/browser/load_instrument", load_instrument)
        self.osc_server.add_handler("/live/browser/load_drum_kit", load_drum_kit)
        self.osc_server.add_handler("/live/browser/load_audio_effect", load_audio_effect)
        self.osc_server.add_handler("/live/browser/load_midi_effect", load_midi_effect)
        self.osc_server.add_handler("/live/browser/load_effect", load_effect)
        self.osc_server.add_handler("/live/browser/load_sound", load_sound)
        self.osc_server.add_handler("/live/browser/load_sample", load_sample)
        self.osc_server.add_handler("/live/browser/load_plugin", load_plugin)
        self.osc_server.add_handler("/live/browser/load_max_device", load_max_device)
        self.osc_server.add_handler("/live/browser/load_user_preset", load_user_preset)

        # Load by target
        self.osc_server.add_handler("/live/browser/load_to_slot", load_to_slot)
        self.osc_server.add_handler("/live/browser/load_to_arrangement", load_to_arrangement)

        # Discovery
        self.osc_server.add_handler("/live/browser/get/categories", get_categories)
        self.osc_server.add_handler("/live/browser/get/children", get_children)
        self.osc_server.add_handler("/live/browser/search", search)
        self.osc_server.add_handler("/live/browser/list_audio_effects", list_audio_effects)
        self.osc_server.add_handler("/live/browser/list_midi_effects", list_midi_effects)
        self.osc_server.add_handler("/live/browser/list_sounds", list_sounds)
        self.osc_server.add_handler("/live/browser/list_plugins", list_plugins)
        self.osc_server.add_handler("/live/browser/list_user_presets", list_user_presets)

        # Preview
        self.osc_server.add_handler("/live/browser/preview", preview)
        self.osc_server.add_handler("/live/browser/stop_preview", stop_preview)

        # Utility
        self.osc_server.add_handler("/live/browser/refresh", refresh)
        self.osc_server.add_handler("/live/browser/hotswap_start", hotswap_start)
        self.osc_server.add_handler("/live/browser/hotswap_load", hotswap_load)
