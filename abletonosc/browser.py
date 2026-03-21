"""
Browser handler for AbletonOSC.
Exposes Live's Browser API for loading audio files into the session.
"""

import Live
import os
from typing import Tuple, Optional, List
from .handler import AbletonOSCHandler


class BrowserHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"
    
    def init_api(self):
        # Get user folders
        self.osc_server.add_handler("/live/browser/get/user_folders", self._get_user_folders)
        
        # Get samples root
        self.osc_server.add_handler("/live/browser/get/samples", self._get_samples)
        
        # List items in a browser item (by path)
        self.osc_server.add_handler("/live/browser/list", self._list_items)
        
        # Load an item by navigating to it
        self.osc_server.add_handler("/live/browser/load", self._load_item)
        
        # Preview an item
        self.osc_server.add_handler("/live/browser/preview", self._preview_item)
        
        # Stop preview
        self.osc_server.add_handler("/live/browser/stop_preview", self._stop_preview)
        
        # Load file directly to selected track
        self.osc_server.add_handler("/live/browser/load_file", self._load_file_to_track)
        
        # Load file to specific session clip slot
        self.osc_server.add_handler("/live/browser/load_to_slot", self._load_to_session_slot)
        
        # Load file to arrangement view at specific position
        self.osc_server.add_handler("/live/browser/load_to_arrangement", self._load_to_arrangement)

    def _get_browser(self):
        """Get the Live browser instance."""
        return Live.Application.get_application().browser

    def _get_user_folders(self, params) -> Tuple:
        """Get list of user folder names."""
        browser = self._get_browser()
        folders = []
        for item in browser.user_folders:
            folders.append(item.name)
        return tuple(folders)

    def _get_samples(self, params) -> Tuple:
        """Get samples browser item children."""
        browser = self._get_browser()
        samples = browser.samples
        items = []
        for child in samples.children:
            items.append(child.name)
        return tuple(items)

    def _find_item_by_path(self, path_parts: List[str], start_item=None):
        """
        Navigate through browser hierarchy to find an item.
        path_parts: list of folder/file names to navigate through
        """
        browser = self._get_browser()
        
        if start_item is None:
            # Start from user_folders or samples based on first path part
            first = path_parts[0].lower()
            if first == "samples":
                current = browser.samples
                path_parts = path_parts[1:]
            elif first == "user library":
                current = browser.user_library
                path_parts = path_parts[1:]
            else:
                # Try to find in user_folders
                current = None
                for folder in browser.user_folders:
                    if folder.name.lower() == first:
                        current = folder
                        path_parts = path_parts[1:]
                        break
                if current is None:
                    return None
        else:
            current = start_item
        
        # Navigate through the path
        for part in path_parts:
            found = False
            for child in current.children:
                if child.name.lower() == part.lower():
                    current = child
                    found = True
                    break
            if not found:
                return None
        
        return current

    def _list_items(self, params) -> Tuple:
        """
        List items at a given path.
        params[0]: path (e.g., "Samples/Drums" or "User Library/My Folder")
        """
        if not params:
            return ("error", "No path provided")
        
        path = params[0]
        path_parts = [p.strip() for p in path.split("/") if p.strip()]
        
        item = self._find_item_by_path(path_parts)
        if item is None:
            return ("error", f"Path not found: {path}")
        
        children = []
        for child in item.children:
            children.append(child.name)
        
        return tuple(children)

    def _load_item(self, params) -> Tuple:
        """
        Load an item by path.
        params[0]: path to the item (e.g., "User Library/Stems/kick.wav")
        """
        if not params:
            return ("error", "No path provided")
        
        path = params[0]
        path_parts = [p.strip() for p in path.split("/") if p.strip()]
        
        item = self._find_item_by_path(path_parts)
        if item is None:
            return ("error", f"Item not found: {path}")
        
        if not item.is_loadable:
            return ("error", f"Item is not loadable: {path}")
        
        browser = self._get_browser()
        browser.load_item(item)
        
        return ("success", f"Loaded: {item.name}")

    def _preview_item(self, params) -> Tuple:
        """
        Preview an item by path.
        params[0]: path to the item
        """
        if not params:
            return ("error", "No path provided")
        
        path = params[0]
        path_parts = [p.strip() for p in path.split("/") if p.strip()]
        
        item = self._find_item_by_path(path_parts)
        if item is None:
            return ("error", f"Item not found: {path}")
        
        browser = self._get_browser()
        browser.preview_item(item)
        
        return ("success", f"Previewing: {item.name}")

    def _stop_preview(self, params) -> Tuple:
        """Stop any current preview."""
        browser = self._get_browser()
        browser.stop_preview()
        return ("success", "Preview stopped")

    def _load_file_to_track(self, params) -> Tuple:
        """
        Load an audio file to the currently selected track.
        This is a convenience method that:
        1. Finds the file in the browser
        2. Loads it to the selected track's first empty clip slot
        
        params[0]: Full file path or browser path
        """
        if not params:
            return ("error", "No file path provided")
        
        file_path = params[0]
        
        # If it's an absolute file path, we need to find it in the browser
        # This requires the file to be in a location Live can see (user folders, samples, etc.)
        if os.path.isabs(file_path):
            # Extract filename
            filename = os.path.basename(file_path)
            # For now, return guidance - full implementation would need to search
            return ("error", f"Absolute paths not yet supported. Add the folder to Live's browser first, then use: /live/browser/load 'FolderName/{filename}'")
        
        # Treat as browser path
        path_parts = [p.strip() for p in file_path.split("/") if p.strip()]
        
        item = self._find_item_by_path(path_parts)
        if item is None:
            return ("error", f"Item not found: {file_path}")
        
        if not item.is_loadable:
            return ("error", f"Item is not loadable: {file_path}")
        
        browser = self._get_browser()
        browser.load_item(item)
        
        return ("success", f"Loaded to selected track: {item.name}")
    
    def _load_to_session_slot(self, params) -> Tuple:
        """
        Load an audio file to a specific clip slot in Session view.
        
        params[0]: Browser path to the audio file
        params[1]: Track index (0-based)
        params[2]: Scene/slot index (0-based)
        """
        if len(params) < 3:
            return ("error", "Required: path, track_index, slot_index")
        
        file_path = params[0]
        track_index = int(params[1])
        slot_index = int(params[2])
        
        # Find the browser item
        path_parts = [p.strip() for p in file_path.split("/") if p.strip()]
        item = self._find_item_by_path(path_parts)
        if item is None:
            return ("error", f"Item not found: {file_path}")
        
        if not item.is_loadable:
            return ("error", f"Item is not loadable: {file_path}")
        
        # Get the song and set up the target
        song = self.song
        app = Live.Application.get_application()
        
        # Ensure we're in Session view
        app.view.show_view("Session")
        app.view.focus_view("Session")
        
        # Select the track and scene to highlight the clip slot
        track = song.tracks[track_index]
        scene = song.scenes[slot_index]
        
        song.view.selected_track = track
        song.view.selected_scene = scene
        
        # Set the highlighted clip slot - this is the key!
        clip_slot = track.clip_slots[slot_index]
        song.view.highlighted_clip_slot = clip_slot
        
        # Now load - it should go to the highlighted slot
        browser = self._get_browser()
        browser.load_item(item)
        
        return ("success", f"Loaded {item.name} to track {track_index}, slot {slot_index}")

    def _load_to_arrangement(self, params) -> Tuple:
        """
        Load an audio file to the Arrangement view at a specific position.
        
        params[0]: Browser path to the audio file
        params[1]: Track index (0-based)
        params[2]: Time position in beats (optional, defaults to current song time)
        """
        if len(params) < 2:
            return ("error", "Required: path, track_index [, time_in_beats]")
        
        file_path = params[0]
        track_index = int(params[1])
        time_position = float(params[2]) if len(params) > 2 else None
        
        # Find the browser item
        path_parts = [p.strip() for p in file_path.split("/") if p.strip()]
        item = self._find_item_by_path(path_parts)
        if item is None:
            return ("error", f"Item not found: {file_path}")
        
        if not item.is_loadable:
            return ("error", f"Item is not loadable: {file_path}")
        
        # Get the song and set up the target
        song = self.song
        app = Live.Application.get_application()
        
        # Switch to Arrangement view
        app.view.show_view("Arranger")
        app.view.focus_view("Arranger")
        
        # Select the track
        track = song.tracks[track_index]
        song.view.selected_track = track
        
        # Set the song time position if specified
        if time_position is not None:
            song.current_song_time = time_position
        
        # Load - should go to arrangement at the current position
        browser = self._get_browser()
        browser.load_item(item)
        
        pos = time_position if time_position is not None else song.current_song_time
        return ("success", f"Loaded {item.name} to track {track_index} at beat {pos}")
