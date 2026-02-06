"""Browser handler for loading devices and presets."""

from typing import Tuple, Any
from .handler import AbletonOSCHandler


class BrowserHandler(AbletonOSCHandler):
    """Handler for browser operations like loading instruments and effects."""

    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"

    def init_api(self):
        """Initialize browser API endpoints."""
        self.osc_server.add_handler("/live/browser/load_instrument",
                                    self._load_instrument)
        self.osc_server.add_handler("/live/browser/load_drum_kit",
                                    self._load_drum_kit)
        self.osc_server.add_handler("/live/browser/load_default_instrument",
                                    self._load_default_instrument)
        # Audio & MIDI effects
        self.osc_server.add_handler("/live/browser/load_audio_effect",
                                    self._load_audio_effect)
        self.osc_server.add_handler("/live/browser/load_midi_effect",
                                    self._load_midi_effect)
        self.osc_server.add_handler("/live/browser/load_default_audio_effect",
                                    self._load_default_audio_effect)
        self.osc_server.add_handler("/live/browser/load_default_midi_effect",
                                    self._load_default_midi_effect)
        self.osc_server.add_handler("/live/browser/list_audio_effects",
                                    self._list_audio_effects)
        self.osc_server.add_handler("/live/browser/list_midi_effects",
                                    self._list_midi_effects)
        # Sounds & Presets
        self.osc_server.add_handler("/live/browser/load_sound",
                                    self._load_sound)
        self.osc_server.add_handler("/live/browser/list_sounds",
                                    self._list_sounds)
        # Samples & Clips
        self.osc_server.add_handler("/live/browser/load_sample",
                                    self._load_sample)
        self.osc_server.add_handler("/live/browser/load_clip",
                                    self._load_clip)
        self.osc_server.add_handler("/live/browser/list_samples",
                                    self._list_samples)
        self.osc_server.add_handler("/live/browser/list_clips",
                                    self._list_clips)
        # Plugins & Max4Live
        self.osc_server.add_handler("/live/browser/load_plugin",
                                    self._load_plugin)
        self.osc_server.add_handler("/live/browser/load_max_device",
                                    self._load_max_device)
        self.osc_server.add_handler("/live/browser/list_plugins",
                                    self._list_plugins)
        self.osc_server.add_handler("/live/browser/list_max_devices",
                                    self._list_max_devices)
        # Browser navigation
        self.osc_server.add_handler("/live/browser/browse",
                                    self._browse)
        self.osc_server.add_handler("/live/browser/browse_path",
                                    self._browse_path)
        self.osc_server.add_handler("/live/browser/search",
                                    self._search)
        self.osc_server.add_handler("/live/browser/get_item_info",
                                    self._get_item_info)
        # User library
        self.osc_server.add_handler("/live/browser/list_user_presets",
                                    self._list_user_presets)
        self.osc_server.add_handler("/live/browser/load_user_preset",
                                    self._load_user_preset)
        # Hotswap & Preview
        self.osc_server.add_handler("/live/browser/hotswap_start",
                                    self._hotswap_start)
        self.osc_server.add_handler("/live/browser/hotswap_load",
                                    self._hotswap_load)
        self.osc_server.add_handler("/live/browser/preview_sample",
                                    self._preview_sample)
        self.osc_server.add_handler("/live/browser/stop_preview",
                                    self._stop_preview)

    @property
    def browser(self):
        """Get the application browser."""
        return self.manager.application.browser

    def _find_item_by_name(self, parent, name: str):
        """Recursively find a browser item by name."""
        for item in parent.children:
            if item.name.lower() == name.lower():
                return item
            # Search in children
            if item.children:
                found = self._find_item_by_name(item, name)
                if found:
                    return found
        return None

    def _get_first_loadable_child(self, item):
        """Get the first loadable item from a browser item's children."""
        if item.is_loadable:
            return item
        for child in item.children:
            if child.is_loadable:
                return child
            found = self._get_first_loadable_child(child)
            if found:
                return found
        return None

    def _load_from_category(self, category, name: str, category_name: str):
        """Generic method to load an item by name from a browser category."""
        item = self._find_item_by_name(category, name)
        if not item:
            self.logger.warning(f"{category_name} not found: {name}")
            return None

        loadable = self._get_first_loadable_child(item)
        if not loadable:
            self.logger.warning(f"No loadable item found for {category_name}: {name}")
            return None

        self.browser.load_item(loadable)
        self.logger.info(f"Loaded {category_name}: {loadable.name}")
        return (loadable.name,)

    def _load_first_from_preferred(self, category, preferred_names: list, category_name: str):
        """Load the first available item from a list of preferred names."""
        for name in preferred_names:
            item = self._find_item_by_name(category, name)
            if item:
                loadable = self._get_first_loadable_child(item)
                if loadable:
                    self.browser.load_item(loadable)
                    self.logger.info(f"Loaded default {category_name}: {loadable.name}")
                    return (loadable.name,)

        # Fallback: try to load any item from category
        loadable = self._get_first_loadable_child(category)
        if loadable:
            self.browser.load_item(loadable)
            self.logger.info(f"Loaded {category_name}: {loadable.name}")
            return (loadable.name,)

        self.logger.warning(f"No default {category_name} found")
        return None

    def _list_category_children(self, category, category_name: str):
        """List names of children in a browser category."""
        names = [item.name for item in category.children]
        self.logger.info(f"Found {len(names)} {category_name}")
        return tuple(names)

    def _load_instrument(self, params: Tuple[Any]):
        """
        Load an instrument by name onto the selected track.

        Usage: /live/browser/load_instrument <instrument_name>
        Example: /live/browser/load_instrument "Simpler"
        """
        if len(params) < 1:
            self.logger.error("load_instrument requires instrument name")
            return

        name = str(params[0])
        self.logger.info(f"Loading instrument: {name}")

        try:
            # Navigate to Instruments in the browser
            browser = self.browser
            instruments = None

            # Find Instruments folder
            for item in browser.instruments.children:
                if name.lower() in item.name.lower():
                    instruments = item
                    break

            if not instruments:
                # Try searching in all instruments
                instruments = self._find_item_by_name(browser.instruments, name)

            if instruments:
                # Get a loadable item
                loadable = self._get_first_loadable_child(instruments)
                if loadable:
                    browser.load_item(loadable)
                    self.logger.info(f"Loaded: {loadable.name}")
                    return (loadable.name,)
                else:
                    self.logger.warning(f"No loadable item found for: {name}")
            else:
                self.logger.warning(f"Instrument not found: {name}")

        except Exception as e:
            self.logger.error(f"Error loading instrument: {e}")

    def _load_drum_kit(self, params: Tuple[Any]):
        """
        Load a drum kit onto the selected track.

        Usage: /live/browser/load_drum_kit [kit_name]
        Example: /live/browser/load_drum_kit "808"
        """
        try:
            browser = self.browser
            drums = browser.drums

            if len(params) > 0:
                name = str(params[0])
                item = self._find_item_by_name(drums, name)
            else:
                # Load first available drum kit
                item = self._get_first_loadable_child(drums)

            if item and item.is_loadable:
                browser.load_item(item)
                self.logger.info(f"Loaded drum kit: {item.name}")
                return (item.name,)
            else:
                self.logger.warning("No drum kit found")

        except Exception as e:
            self.logger.error(f"Error loading drum kit: {e}")

    def _load_default_instrument(self, params: Tuple[Any]):
        """
        Load a default instrument onto the selected track.
        Prefers synthesizers (Drift, Analog, Wavetable) over samplers (Simpler)
        because synths produce sound immediately without needing samples.

        Usage: /live/browser/load_default_instrument
        """
        try:
            # Prefer synths over samplers - synths make sound without samples
            preferred = ["Drift", "Analog", "Wavetable", "Operator", "Tension", "Collision"]
            return self._load_first_from_preferred(
                self.browser.instruments, preferred, "instrument"
            )
        except Exception as e:
            self.logger.error(f"Error loading default instrument: {e}")

    # =========================================================================
    # Audio & MIDI Effects
    # =========================================================================

    def _load_audio_effect(self, params: Tuple[Any]):
        """
        Load an audio effect by name onto the selected track.

        Usage: /live/browser/load_audio_effect <effect_name>
        Example: /live/browser/load_audio_effect "Reverb"
        """
        if len(params) < 1:
            self.logger.error("load_audio_effect requires effect name")
            return
        try:
            return self._load_from_category(
                self.browser.audio_effects, str(params[0]), "audio effect"
            )
        except Exception as e:
            self.logger.error(f"Error loading audio effect: {e}")

    def _load_midi_effect(self, params: Tuple[Any]):
        """
        Load a MIDI effect by name onto the selected track.

        Usage: /live/browser/load_midi_effect <effect_name>
        Example: /live/browser/load_midi_effect "Arpeggiator"
        """
        if len(params) < 1:
            self.logger.error("load_midi_effect requires effect name")
            return
        try:
            return self._load_from_category(
                self.browser.midi_effects, str(params[0]), "MIDI effect"
            )
        except Exception as e:
            self.logger.error(f"Error loading MIDI effect: {e}")

    def _load_default_audio_effect(self, params: Tuple[Any]):
        """
        Load a default audio effect (Reverb) onto the selected track.

        Usage: /live/browser/load_default_audio_effect
        """
        try:
            preferred = ["Reverb", "Delay", "EQ Eight", "Compressor", "Utility"]
            return self._load_first_from_preferred(
                self.browser.audio_effects, preferred, "audio effect"
            )
        except Exception as e:
            self.logger.error(f"Error loading default audio effect: {e}")

    def _load_default_midi_effect(self, params: Tuple[Any]):
        """
        Load a default MIDI effect (Arpeggiator) onto the selected track.

        Usage: /live/browser/load_default_midi_effect
        """
        try:
            preferred = ["Arpeggiator", "Chord", "Scale", "Note Length", "Pitch"]
            return self._load_first_from_preferred(
                self.browser.midi_effects, preferred, "MIDI effect"
            )
        except Exception as e:
            self.logger.error(f"Error loading default MIDI effect: {e}")

    def _list_audio_effects(self, params: Tuple[Any]):
        """
        List available audio effects.

        Usage: /live/browser/list_audio_effects
        Returns: Tuple of effect names
        """
        try:
            return self._list_category_children(
                self.browser.audio_effects, "audio effect categories"
            )
        except Exception as e:
            self.logger.error(f"Error listing audio effects: {e}")
            return ()

    def _list_midi_effects(self, params: Tuple[Any]):
        """
        List available MIDI effects.

        Usage: /live/browser/list_midi_effects
        Returns: Tuple of effect names
        """
        try:
            return self._list_category_children(
                self.browser.midi_effects, "MIDI effect categories"
            )
        except Exception as e:
            self.logger.error(f"Error listing MIDI effects: {e}")
            return ()

    # =========================================================================
    # Sounds & Presets
    # =========================================================================

    def _load_sound(self, params: Tuple[Any]):
        """
        Load a sound preset by name onto the selected track.

        Usage: /live/browser/load_sound <sound_name>
        Example: /live/browser/load_sound "Bass"
        """
        if len(params) < 1:
            self.logger.error("load_sound requires sound name")
            return
        try:
            return self._load_from_category(
                self.browser.sounds, str(params[0]), "sound"
            )
        except Exception as e:
            self.logger.error(f"Error loading sound: {e}")

    def _list_sounds(self, params: Tuple[Any]):
        """
        List available sound presets.

        Usage: /live/browser/list_sounds
        Returns: Tuple of sound category names
        """
        try:
            return self._list_category_children(
                self.browser.sounds, "sound categories"
            )
        except Exception as e:
            self.logger.error(f"Error listing sounds: {e}")
            return ()

    # =========================================================================
    # Samples & Clips
    # =========================================================================

    def _load_sample(self, params: Tuple[Any]):
        """
        Load a sample by name onto the selected track (via Simpler).

        Usage: /live/browser/load_sample <sample_name>
        Example: /live/browser/load_sample "kick"
        """
        if len(params) < 1:
            self.logger.error("load_sample requires sample name")
            return
        try:
            return self._load_from_category(
                self.browser.samples, str(params[0]), "sample"
            )
        except Exception as e:
            self.logger.error(f"Error loading sample: {e}")

    def _load_clip(self, params: Tuple[Any]):
        """
        Load a clip by name.

        Usage: /live/browser/load_clip <clip_name>
        Example: /live/browser/load_clip "drums"
        """
        if len(params) < 1:
            self.logger.error("load_clip requires clip name")
            return
        try:
            return self._load_from_category(
                self.browser.clips, str(params[0]), "clip"
            )
        except Exception as e:
            self.logger.error(f"Error loading clip: {e}")

    def _list_samples(self, params: Tuple[Any]):
        """
        List available samples.

        Usage: /live/browser/list_samples [category]
        Returns: Tuple of sample names
        """
        try:
            browser = self.browser
            category = str(params[0]) if len(params) > 0 else None

            if category:
                parent = self._find_item_by_name(browser.samples, category)
                if not parent:
                    self.logger.warning(f"Sample category not found: {category}")
                    return ()
            else:
                parent = browser.samples

            samples = []
            for item in parent.children:
                samples.append(item.name)
            self.logger.info(f"Found {len(samples)} samples")
            return tuple(samples)

        except Exception as e:
            self.logger.error(f"Error listing samples: {e}")
            return ()

    def _list_clips(self, params: Tuple[Any]):
        """
        List available clips.

        Usage: /live/browser/list_clips [category]
        Returns: Tuple of clip names
        """
        try:
            browser = self.browser
            category = str(params[0]) if len(params) > 0 else None

            if category:
                parent = self._find_item_by_name(browser.clips, category)
                if not parent:
                    self.logger.warning(f"Clip category not found: {category}")
                    return ()
            else:
                parent = browser.clips

            clips = []
            for item in parent.children:
                clips.append(item.name)
            self.logger.info(f"Found {len(clips)} clips")
            return tuple(clips)

        except Exception as e:
            self.logger.error(f"Error listing clips: {e}")
            return ()

    # =========================================================================
    # Plugins & Max4Live
    # =========================================================================

    def _load_plugin(self, params: Tuple[Any]):
        """
        Load a VST/AU plugin by name onto the selected track.

        Usage: /live/browser/load_plugin <plugin_name>
        Example: /live/browser/load_plugin "Serum"
        """
        if len(params) < 1:
            self.logger.error("load_plugin requires plugin name")
            return
        try:
            return self._load_from_category(
                self.browser.plugins, str(params[0]), "plugin"
            )
        except Exception as e:
            self.logger.error(f"Error loading plugin: {e}")

    def _load_max_device(self, params: Tuple[Any]):
        """
        Load a Max for Live device by name onto the selected track.

        Usage: /live/browser/load_max_device <device_name>
        Example: /live/browser/load_max_device "LFO"
        """
        if len(params) < 1:
            self.logger.error("load_max_device requires device name")
            return
        try:
            return self._load_from_category(
                self.browser.max_for_live, str(params[0]), "Max device"
            )
        except Exception as e:
            self.logger.error(f"Error loading Max device: {e}")

    def _list_plugins(self, params: Tuple[Any]):
        """
        List available VST/AU plugins.

        Usage: /live/browser/list_plugins
        Returns: Tuple of plugin names
        """
        try:
            return self._list_category_children(self.browser.plugins, "plugins")
        except Exception as e:
            self.logger.error(f"Error listing plugins: {e}")
            return ()

    def _list_max_devices(self, params: Tuple[Any]):
        """
        List available Max for Live devices.

        Usage: /live/browser/list_max_devices
        Returns: Tuple of M4L device names
        """
        try:
            return self._list_category_children(
                self.browser.max_for_live, "Max for Live devices"
            )
        except Exception as e:
            self.logger.error(f"Error listing Max for Live devices: {e}")
            return ()

    # =========================================================================
    # Browser Navigation
    # =========================================================================

    def _get_category(self, category: str):
        """Get a browser category by name."""
        browser = self.browser
        category_map = {
            "instruments": browser.instruments,
            "drums": browser.drums,
            "sounds": browser.sounds,
            "audio_effects": browser.audio_effects,
            "midi_effects": browser.midi_effects,
            "max_for_live": browser.max_for_live,
            "plugins": browser.plugins,
            "clips": browser.clips,
            "samples": browser.samples,
            "packs": browser.packs,
            "user_library": browser.user_library,
            "current_project": browser.current_project,
        }
        return category_map.get(category.lower())

    def _browse(self, params: Tuple[Any]):
        """
        Browse a top-level browser category.

        Usage: /live/browser/browse <category>
        Example: /live/browser/browse "instruments"
        Categories: instruments, drums, sounds, audio_effects, midi_effects,
                   max_for_live, plugins, clips, samples, packs, user_library
        Returns: Tuple of item names in that category
        """
        if len(params) < 1:
            self.logger.error("browse requires category name")
            return ()

        category = str(params[0])
        self.logger.info(f"Browsing category: {category}")

        try:
            parent = self._get_category(category)
            if not parent:
                self.logger.warning(f"Unknown category: {category}")
                return ()

            items = []
            for item in parent.children:
                items.append(item.name)
            self.logger.info(f"Found {len(items)} items in {category}")
            return tuple(items)

        except Exception as e:
            self.logger.error(f"Error browsing: {e}")
            return ()

    def _browse_path(self, params: Tuple[Any]):
        """
        Browse a specific path in the browser.

        Usage: /live/browser/browse_path <category> <path>
        Example: /live/browser/browse_path "instruments" "Drift"
        Returns: Tuple of item names at that path
        """
        if len(params) < 2:
            self.logger.error("browse_path requires category and path")
            return ()

        category = str(params[0])
        path = str(params[1])
        self.logger.info(f"Browsing path: {category}/{path}")

        try:
            parent = self._get_category(category)
            if not parent:
                self.logger.warning(f"Unknown category: {category}")
                return ()

            item = self._find_item_by_name(parent, path)
            if not item:
                self.logger.warning(f"Path not found: {path}")
                return ()

            items = []
            for child in item.children:
                items.append(child.name)
            self.logger.info(f"Found {len(items)} items at {path}")
            return tuple(items)

        except Exception as e:
            self.logger.error(f"Error browsing path: {e}")
            return ()

    def _search(self, params: Tuple[Any]):
        """
        Search for items across the browser.

        Usage: /live/browser/search <query>
        Example: /live/browser/search "bass"
        Returns: Tuple of (category, name) pairs for matches
        """
        if len(params) < 1:
            self.logger.error("search requires a query")
            return ()

        query = str(params[0]).lower()
        self.logger.info(f"Searching browser for: {query}")

        try:
            browser = self.browser
            results = []

            # Search in all categories
            categories = [
                ("instruments", browser.instruments),
                ("drums", browser.drums),
                ("sounds", browser.sounds),
                ("audio_effects", browser.audio_effects),
                ("midi_effects", browser.midi_effects),
                ("plugins", browser.plugins),
                ("clips", browser.clips),
                ("samples", browser.samples),
            ]

            for cat_name, category in categories:
                matches = self._search_in_category(category, query, cat_name)
                results.extend(matches[:10])  # Limit per category

            self.logger.info(f"Found {len(results)} search results")
            # Flatten to alternating category, name pairs
            flat_results = []
            for cat, name in results[:50]:  # Total limit
                flat_results.extend([cat, name])
            return tuple(flat_results)

        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return ()

    def _search_in_category(self, parent, query: str, category: str, depth: int = 0):
        """Recursively search for items matching query."""
        results = []
        if depth > 3:  # Limit recursion depth
            return results

        for item in parent.children:
            if query in item.name.lower():
                results.append((category, item.name))
            if item.children:
                results.extend(self._search_in_category(item, query, category, depth + 1))
        return results

    def _get_item_info(self, params: Tuple[Any]):
        """
        Get information about a browser item.

        Usage: /live/browser/get_item_info <category> <name>
        Example: /live/browser/get_item_info "instruments" "Drift"
        Returns: Tuple of (name, is_loadable, is_device, has_children, child_count)
        """
        if len(params) < 2:
            self.logger.error("get_item_info requires category and name")
            return ()

        category = str(params[0])
        name = str(params[1])
        self.logger.info(f"Getting info for: {category}/{name}")

        try:
            parent = self._get_category(category)
            if not parent:
                self.logger.warning(f"Unknown category: {category}")
                return ()

            item = self._find_item_by_name(parent, name)
            if not item:
                self.logger.warning(f"Item not found: {name}")
                return ()

            child_count = len(item.children) if item.children else 0
            return (
                item.name,
                item.is_loadable,
                item.is_device,
                child_count > 0,
                child_count
            )

        except Exception as e:
            self.logger.error(f"Error getting item info: {e}")
            return ()

    # =========================================================================
    # User Library
    # =========================================================================

    def _list_user_presets(self, params: Tuple[Any]):
        """
        List presets in the user library.

        Usage: /live/browser/list_user_presets [category]
        Example: /live/browser/list_user_presets "Presets"
        Returns: Tuple of preset names
        """
        try:
            browser = self.browser
            category = str(params[0]) if len(params) > 0 else None

            if category:
                parent = self._find_item_by_name(browser.user_library, category)
                if not parent:
                    self.logger.warning(f"User library category not found: {category}")
                    return ()
            else:
                parent = browser.user_library

            presets = []
            for item in parent.children:
                presets.append(item.name)
            self.logger.info(f"Found {len(presets)} user presets")
            return tuple(presets)

        except Exception as e:
            self.logger.error(f"Error listing user presets: {e}")
            return ()

    def _load_user_preset(self, params: Tuple[Any]):
        """
        Load a preset from the user library.

        Usage: /live/browser/load_user_preset <preset_path>
        Example: /live/browser/load_user_preset "My Preset"
        """
        if len(params) < 1:
            self.logger.error("load_user_preset requires preset path")
            return

        path = str(params[0])
        self.logger.info(f"Loading user preset: {path}")

        try:
            browser = self.browser
            item = self._find_item_by_name(browser.user_library, path)

            if item:
                loadable = self._get_first_loadable_child(item)
                if loadable:
                    browser.load_item(loadable)
                    self.logger.info(f"Loaded user preset: {loadable.name}")
                    return (loadable.name,)
                elif item.is_loadable:
                    browser.load_item(item)
                    self.logger.info(f"Loaded user preset: {item.name}")
                    return (item.name,)
                else:
                    self.logger.warning(f"No loadable item found for: {path}")
            else:
                self.logger.warning(f"User preset not found: {path}")

        except Exception as e:
            self.logger.error(f"Error loading user preset: {e}")

    # =========================================================================
    # Hotswap & Preview
    # =========================================================================

    def _hotswap_start(self, params: Tuple[Any]):
        """
        Enter hotswap mode for a specific device.

        Usage: /live/browser/hotswap_start <track_index> <device_index>
        Example: /live/browser/hotswap_start 0 0
        """
        if len(params) < 2:
            self.logger.error("hotswap_start requires track and device index")
            return

        try:
            track_index = int(params[0])
            device_index = int(params[1])
            self.logger.info(f"Starting hotswap for track {track_index}, device {device_index}")

            song = self.manager.song
            track = song.tracks[track_index]
            device = track.devices[device_index]

            browser = self.browser
            browser.hotswap_target = device
            self.logger.info(f"Hotswap started for device: {device.name}")
            return (device.name,)

        except Exception as e:
            self.logger.error(f"Error starting hotswap: {e}")

    def _hotswap_load(self, params: Tuple[Any]):
        """
        Load an item via hotswap mode.

        Usage: /live/browser/hotswap_load <name>
        Note: Must call hotswap_start first
        """
        if len(params) < 1:
            self.logger.error("hotswap_load requires item name")
            return

        name = str(params[0])
        self.logger.info(f"Hotswap loading: {name}")

        try:
            browser = self.browser

            if not browser.hotswap_target:
                self.logger.warning("No hotswap target set. Call hotswap_start first.")
                return

            # Search in the appropriate category for the hotswap target
            item = None
            for category in [browser.instruments, browser.audio_effects,
                           browser.midi_effects, browser.sounds]:
                item = self._find_item_by_name(category, name)
                if item:
                    break

            if item:
                loadable = self._get_first_loadable_child(item)
                if loadable:
                    browser.load_item(loadable)
                    self.logger.info(f"Hotswap loaded: {loadable.name}")
                    return (loadable.name,)
            else:
                self.logger.warning(f"Item not found for hotswap: {name}")

        except Exception as e:
            self.logger.error(f"Error in hotswap load: {e}")

    def _preview_sample(self, params: Tuple[Any]):
        """
        Preview a sample before loading.

        Usage: /live/browser/preview_sample <sample_name>
        Example: /live/browser/preview_sample "kick"
        """
        if len(params) < 1:
            self.logger.error("preview_sample requires sample name")
            return

        name = str(params[0])
        self.logger.info(f"Previewing sample: {name}")

        try:
            browser = self.browser
            item = self._find_item_by_name(browser.samples, name)

            if item:
                loadable = self._get_first_loadable_child(item)
                target = loadable if loadable else item
                if target:
                    browser.preview_item(target)
                    self.logger.info(f"Previewing: {target.name}")
                    return (target.name,)
            else:
                self.logger.warning(f"Sample not found for preview: {name}")

        except Exception as e:
            self.logger.error(f"Error previewing sample: {e}")

    def _stop_preview(self, params: Tuple[Any]):
        """
        Stop sample preview playback.

        Usage: /live/browser/stop_preview
        """
        try:
            browser = self.browser
            browser.stop_preview()
            self.logger.info("Stopped preview")
            return (True,)

        except Exception as e:
            self.logger.error(f"Error stopping preview: {e}")
