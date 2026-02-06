from typing import Tuple, Any
from .handler import AbletonOSCHandler

class ClipSlotHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "clip_slot"

    def init_api(self):
        def create_clip_slot_callback(func, *args, pass_clip_index=False, **kwargs):
            def clip_slot_callback(params: Tuple[Any]):
                track_index, clip_index = int(params[0]), int(params[1])
                track = self.song.tracks[track_index]
                clip_slot = track.clip_slots[clip_index]

                if pass_clip_index:
                    rv = func(clip_slot, *args, tuple(params[0:]), **kwargs)
                else:
                    rv = func(clip_slot, *args, tuple(params[2:]), **kwargs)

                self.logger.info("clip_slot %s,%s -> %s", track_index, clip_index, rv)
                if rv is not None:
                    return (track_index, clip_index, *rv)

            return clip_slot_callback

        methods = {
            "fire":              {"alias": 0, "caller": 1},
            "stop":              {"alias": 0, "caller": 1},
            "create_clip":       {"alias": 0, "caller": 1},   # Back-compat
            "create/midi_clip":  {"alias": 1, "caller": "create_clip"},
            "create/audio_clip": {"alias": 1, "caller": "create_audio_clip"},
            "delete_clip":       {"alias": 0, "caller": 1},   # Back-compat
            "delete/clip":       {"alias": 1, "caller": "delete_clip"},
            "duplicate_to":      {"alias": 0, "caller": "clip_slot_duplicate_to"},
            "set/fire_button":   {"alias": 1, "caller": "set_fire_button_state"},
        }

        properties = {
            # TODO: returns objects, needs serialization
            # "canonical_parent":      {"get": 0, "set": 0, "listen": 0},
            # "clip":                  {"get": 0, "set": 0, "listen": 0},

            # All clip slots
            "has_clip":              {"get": 1, "set": 0, "listen": 1},
            "has_stop_button":       {"get": 1, "set": 1, "listen": 1},
            "is_group_slot":         {"get": 1, "set": 0, "listen": 0},
            "is_playing":            {"get": 1, "set": 0, "listen": 0},
            "is_recording":          {"get": 1, "set": 0, "listen": 0},
            "is_triggered":          {"get": 1, "set": 0, "listen": 1},
            "will_record_on_start":  {"get": 1, "set": 0, "listen": 0},
            
            # Group Track slots only
            "color":                 {"get": 1, "set": 0, "listen": 1},
            "color_index":           {"get": 1, "set": 0, "listen": 1},
            "controls_other_clips":  {"get": 1, "set": 0, "listen": 1},
            "playing_status":        {"get": 1, "set": 0, "listen": 1},


        }

        def clip_slot_duplicate_to(clip_slot, args):
            target_track_index, target_clip_index = tuple(args)
            track = self.song.tracks[target_track_index]
            target_clip_slot = track.clip_slots[target_clip_index]
            clip_slot.duplicate_clip_to(target_clip_slot)

        # Add Handlers
        local_funcs = locals()
        for method, spec in methods.items():
            alias = spec.get("alias")
            caller = spec.get("caller")
            if not caller:
                continue
            if not alias and isinstance(caller, str):
                caller = local_funcs[caller]
                self.osc_server.add_handler("/live/clip_slot/%s" % method,
                                            create_clip_slot_callback(caller))
            else:
                if not alias:
                    caller = method
                self.osc_server.add_handler("/live/clip_slot/%s" % method,
                                            create_clip_slot_callback(self._call_method, caller))

        for prop, spec in properties.items():
            getter_func = spec.get("get")
            if isinstance(getter_func, str):
                getter = local_funcs[getter_func]
                self.osc_server.add_handler("/live/clip_slot/get/%s" % prop,
                                            create_clip_slot_callback(getter))
            elif getter_func:
                self.osc_server.add_handler("/live/clip_slot/get/%s" % prop,
                                            create_clip_slot_callback(self._get_property, prop))

            setter_func = spec.get("set")
            if isinstance(setter_func, str):
                setter = local_funcs[setter_func]
                self.osc_server.add_handler("/live/clip_slot/set/%s" % prop,
                                            create_clip_slot_callback(setter))
            elif setter_func:
                self.osc_server.add_handler("/live/clip_slot/set/%s" % prop,
                                            create_clip_slot_callback(self._set_property, prop))

            observable = spec.get("listen")
            if isinstance(observable, str):
                getter = "bang" if observable == "bang" else local_funcs[observable]
                self.osc_server.add_handler("/live/clip_slot/start_listen/%s" % prop,
                                            create_clip_slot_callback(self._start_listen, prop, pass_clip_index=True, getter=getter))
                self.osc_server.add_handler("/live/clip_slot/stop_listen/%s" % prop,
                                            create_clip_slot_callback(self._stop_listen, prop, pass_clip_index=True))
            elif observable:
                self.osc_server.add_handler("/live/clip_slot/start_listen/%s" % prop,
                                            create_clip_slot_callback(self._start_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/clip_slot/stop_listen/%s" % prop,
                                            create_clip_slot_callback(self._stop_listen, prop, pass_clip_index=True))
