from functools import partial
from typing import Optional, Tuple, Any
from .component import AbletonOSCComponent

import Live
import logging

logger = logging.getLogger("abletonosc")

class ClipSlotComponent(AbletonOSCComponent):
    def init_api(self):
        def create_clip_slot_callback(func, *args):
            def clip_slot_callback(params: Tuple[Any]):
                track_index, clip_index = params[:2]
                track = self.song.tracks[track_index]
                clip_slot = track.clip_slots[clip_index]
                return func(clip_slot, *args)
            return clip_slot_callback

        for method in ["fire", "stop"]:
            self.osc_server.add_handler("/live/clip_slot/%s" % method, create_clip_slot_callback(self._call_method, method))
