from typing import Tuple, Any
from .component import AbletonOSCComponent

class ClipSlotComponent(AbletonOSCComponent):
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
            self.osc_server.add_handler("/live/clip_slot/get_property/%s" % prop,
                                        create_clip_slot_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/clip_slot/start_property_listen/%s" % prop,
                                        create_clip_slot_callback(self._start_property_listen, prop))
            self.osc_server.add_handler("/live/clip_slot/stop_property_listen/%s" % prop,
                                        create_clip_slot_callback(self._stop_property_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/clip_slot/set_property/%s" % prop,
                                        create_clip_slot_callback(self._set_property, prop))
