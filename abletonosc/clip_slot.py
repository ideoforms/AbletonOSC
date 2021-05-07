from typing import Tuple, Any
from .handler import AbletonOSCHandler

class ClipSlotHandler(AbletonOSCHandler):
    def init_api(self):
        def create_clip_slot_callback(func, *args):
            def clip_slot_callback(params: Tuple[Any]):
                track_index, clip_index = params[:2]
                track = self.song.tracks[track_index]
                clip_slot = track.clip_slots[clip_index]
                return func(clip_slot, *args, params[2:])

            return clip_slot_callback

        methods = [
            "fire",
            "stop",
            "create_clip",
            "delete_clip"
        ]
        properties_r = [
            "has_clip",
            "controls_other_clips",
            "is_group_slot",
            "is_playing",
            "is_triggered",
            "playing_status",
            "will_record_on_start",
        ]
        properties_rw = [
            "has_stop_button"
        ]

        for method in methods:
            self.osc_server.add_handler("/live/clip_slot/%s" % method,
                                        create_clip_slot_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/clip_slot/get/%s" % prop,
                                        create_clip_slot_callback(self._get, prop))
            self.osc_server.add_handler("/live/clip_slot/start_listen/%s" % prop,
                                        create_clip_slot_callback(self._start_listen, prop))
            self.osc_server.add_handler("/live/clip_slot/stop_listen/%s" % prop,
                                        create_clip_slot_callback(self._stop_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/clip_slot/set/%s" % prop,
                                        create_clip_slot_callback(self._set, prop))
