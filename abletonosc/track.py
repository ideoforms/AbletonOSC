from typing import Tuple, Any, Callable, Optional
from .handler import AbletonOSCHandler


class TrackHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "track"

    def init_api(self):
        def create_track_callback(func: Callable,
                                  *args,
                                  include_track_id: bool = False):
            def track_callback(params: Tuple[Any]):
                if params[0] == "*":
                    track_indices = list(range(len(self.song.tracks)))
                else:
                    track_indices = [int(params[0])]

                for track_index in track_indices:
                    track = self.song.tracks[track_index]
                    if include_track_id:
                        rv = func(track, *args, tuple([track_index] + params[1:]))
                    else:
                        rv = func(track, *args, tuple(params[1:]))

                    if rv is not None:
                        return (track_index, *rv)

            return track_callback

        methods = {
            "delete_device":                    {"alias": 0, "caller": 1},
            "delete_clip":                      {"alias": 0, "caller": "track_delete_clip"},  # Shortcut to clip slot delete
            "stop_all_clips":                   {"alias": 0, "caller": 1},
            "duplicate_clip_to_arrangement":    {"alias": 0, "caller": "track_duplicate_clip_to_arrangement"},
            # New
            "delete/device":                    {"alias": 1, "caller": "delete_device"},
            "delete/clip":                      {"alias": 0, "caller": "track_delete_clip"},
            "delete/arrangement_clip":          {"alias": 0, "caller": "track_delete_arrangement_clip"},
            "duplicate/clip_to_arrangement":    {"alias": 0, "caller": "track_duplicate_clip_to_arrangement"},
            "duplicate/clip_slot":              {"alias": 1, "caller": "duplicate_clip_slot"},
            "stop/all_clips":                   {"alias": 1, "caller": "stop_all_clips"},
            "create/audio_clip":                {"alias": 1, "caller": "create_audio_clip"},
            "create/midi_clip":                 {"alias": 1, "caller": "create_midi_clip"},
            "jump_in_running_session_clip":     {"alias": 0, "caller": 1},
        }
        properties = {
            "can_be_armed":             {"get": 1, "set": 0, "listen": 0},  # listener removed
            "can_be_frozen":            {"get": 1, "set": 0, "listen": 0},
            "can_show_chains":          {"get": 1, "set": 0, "listen": 0},
            "fired_slot_index":         {"get": 1, "set": 0, "listen": 1},
            "has_audio_input":          {"get": 1, "set": 0, "listen": 1},
            "has_audio_output":         {"get": 1, "set": 0, "listen": 1},
            "has_midi_input":           {"get": 1, "set": 0, "listen": 1},
            "has_midi_output":          {"get": 1, "set": 0, "listen": 1},
            "input_meter_level":        {"get": 1, "set": 0, "listen": 1},
            "input_meter_left":         {"get": 1, "set": 0, "listen": 1},
            "input_meter_right":        {"get": 1, "set": 0, "listen": 1},
            "is_foldable":              {"get": 1, "set": 0, "listen": 0},  # listener removed
            "is_frozen":                {"get": 1, "set": 0, "listen": 1},
            "is_grouped":               {"get": 1, "set": 0, "listen": 0},  # listener removed
            "is_part_of_selection":     {"get": 1, "set": 0, "listen": 0},
            "is_visible":               {"get": 1, "set": 0, "listen": 0},  # listener removed
            "muted_via_solo":           {"get": 1, "set": 0, "listen": 1},
            "output_meter_level":       {"get": 1, "set": 0, "listen": 1},
            "output_meter_left":        {"get": 1, "set": 0, "listen": 1},
            "output_meter_right":       {"get": 1, "set": 0, "listen": 1},
            "performance_impact":       {"get": 1, "set": 0, "listen": 1},
            "playing_slot_index":       {"get": 1, "set": 0, "listen": 1},
            "arm":                      {"get": 1, "set": 1, "listen": 1},
            "back_to_arranger":         {"get": 1, "set": 1, "listen": 1},
            "color":                    {"get": 1, "set": 1, "listen": 1},
            "color_index":              {"get": 1, "set": 1, "listen": 1},
            "current_monitoring_state": {"get": 1, "set": 1, "listen": 1},
            "fold_state":               {"get": 1, "set": 1, "listen": 0},  # listener removed
            "implicit_arm":             {"get": 1, "set": 1, "listen": 1},
            "is_showing_chains":        {"get": 1, "set": 1, "listen": 1},
            "mute":                     {"get": 1, "set": 1, "listen": 1},
            "solo":                     {"get": 1, "set": 1, "listen": 1},
            "name":                     {"get": 1, "set": 1, "listen": 1},
            # Clip lists
            "clips/name":                   {"get": "track_get_clip_names", "set": 0, "listen": 0},
            "clips/length":                 {"get": "track_get_clip_lengths", "set": 0, "listen": 0},
            "clips/color":                  {"get": "track_get_clip_colors", "set": 0, "listen": 0},
            "arrangement_clips/name":       {"get": "track_get_arrangement_clip_names", "set": 0, "listen": 0},
            "arrangement_clips/length":     {"get": "track_get_arrangement_clip_lengths", "set": 0, "listen": 0},
            "arrangement_clips/start_time": {"get": "track_get_arrangement_clip_start_times", "set": 0, "listen": 0},
            # Device lists
            "num_devices":                  {"get": "track_get_num_devices", "set": 0, "listen": 0},
            "devices/name":                 {"get": "track_get_device_names", "set": 0, "listen": 0},
            "devices/type":                 {"get": "track_get_device_types", "set": 0, "listen": 0},
            "devices/class_name":           {"get": "track_get_device_class_names", "set": 0, "listen": 0},
            "devices/can_have_chains":      {"get": "track_get_device_can_have_chains", "set": 0, "listen": 0},
            # Routing
            "available_output_routing_types":       {"get": "track_get_available_output_routing_types", "set": 0, "listen": 0},
            "available_output_routing_channels":    {"get": "track_get_available_output_routing_channels", "set": 0, "listen": 0},
            "output_routing_type":                  {"get": "track_get_output_routing_type", "set": "track_set_output_routing_type", "listen": 0},
            "output_routing_channel":               {"get": "track_get_output_routing_channel", "set": "track_set_output_routing_channel", "listen": 0},
            "available_input_routing_types":        {"get": "track_get_available_input_routing_types", "set": 0, "listen": 0},
            "available_input_routing_channels":     {"get": "track_get_available_input_routing_channels", "set": 0, "listen": 0},
            "input_routing_type":                   {"get": "track_get_input_routing_type", "set": "track_set_input_routing_type", "listen": 0},
            "input_routing_channel":                {"get": "track_get_input_routing_channel", "set": "track_set_input_routing_channel", "listen": 0},
            "input_routings":                       {"get": "track_get_input_routings", "set": 0, "listen": 0},
            "input_sub_routings":                   {"get": "track_get_input_sub_routings", "set": 0, "listen": 0},
            "current_input_routing":                {"get": "track_get_current_input_routing", "set": "track_set_current_input_routing", "listen": 0},
            "current_input_sub_routing":            {"get": "track_get_current_input_sub_routing", "set": "track_set_current_input_sub_routing", "listen": 0},
            "output_routings":                      {"get": "track_get_output_routings", "set": 0, "listen": 0},
            "output_sub_routings":                  {"get": "track_get_output_sub_routings", "set": 0, "listen": 0},
            "current_output_routing":               {"get": "track_get_current_output_routing", "set": "track_set_current_output_routing", "listen": 0},
            "current_output_sub_routing":           {"get": "track_get_current_output_sub_routing", "set": "track_set_current_output_sub_routing", "listen": 0},
            
        }
        
        def track_duplicate_clip_to_arrangement(track, params):
            """
            Duplicate a session clip to arrangement view at a specific time.
            params: (clip_slot_index, time_in_beats)
            """
            clip_slot_index = int(params[0])
            time = float(params[1])
            clip_slot = track.clip_slots[clip_slot_index]
            if clip_slot.clip:
                track.duplicate_clip_to_arrangement(clip_slot.clip, time)
        

        def track_delete_clip(track, params: Tuple[Any]):
            clip_index, = params
            track.clip_slots[clip_index].delete_clip()
            
        def track_delete_arrangement_clip(track, params):
            clip_index, = params
            clip = track.arrangement_clips[clip_index]
            track.delete_clip(clip)



        #--------------------------------------------------------------------------------
        # Track.[Arrangement_]Clip: List Properties
        #--------------------------------------------------------------------------------
        def track_get_clip_names(track, _):
            return tuple(clip_slot.clip.name if clip_slot.clip else None for clip_slot in track.clip_slots)
        def track_get_clip_lengths(track, _):
            return tuple(clip_slot.clip.length if clip_slot.clip else None for clip_slot in track.clip_slots)
        def track_get_clip_colors(track, _):
            return tuple(clip_slot.clip.color if clip_slot.clip else None for clip_slot in track.clip_slots)
        def track_get_arrangement_clip_names(track, _):
            return tuple(clip.name for clip in track.arrangement_clips)
        def track_get_arrangement_clip_lengths(track, _):
            return tuple(clip.length for clip in track.arrangement_clips)
        def track_get_arrangement_clip_start_times(track, _):
            return tuple(clip.start_time for clip in track.arrangement_clips)
        
        #--------------------------------------------------------------------------------
        # Track.Device: List Properties
        # - name: the device's human-readable name
        # - type: 0 = audio_effect, 1 = instrument, 2 = midi_effect
        # - class_name: e.g. Operator, Reverb, AuPluginDevice, PluginDevice, InstrumentGroupDevice
        #--------------------------------------------------------------------------------
        def track_get_num_devices(track, _):
            return len(track.devices),
        def track_get_device_names(track, _):
            return tuple(device.name for device in track.devices)
        def track_get_device_types(track, _):
            return tuple(device.type for device in track.devices)
        def track_get_device_class_names(track, _):
            return tuple(device.class_name for device in track.devices)
        def track_get_device_can_have_chains(track, _):
            return tuple(device.can_have_chains for device in track.devices)
        
        #--------------------------------------------------------------------------------
        # Track: Output routing.
        # An output route has a type (e.g. "Ext. Out") and a channel (e.g. "1/2").
        # Since Live 10, both of these need to be set by reference to the appropriate
        # item in the available_output_routing_types vector.
        #--------------------------------------------------------------------------------
        def _routing_display_names(items) -> Tuple[str, ...]:
            names = []
            for item in items:
                name = getattr(item, "display_name", None)
                names.append(name if name is not None else str(item))
            return tuple(names)

        def track_get_available_output_routing_types(track, _):
            return _routing_display_names(track.available_output_routing_types)
        def track_get_available_output_routing_channels(track, _):
            return _routing_display_names(track.available_output_routing_channels)
        def track_get_output_routing_type(track, _):
            return track.output_routing_type.display_name,
        def track_set_output_routing_type(track, params):
            type_name = str(params[0])
            for routing_type in track.available_output_routing_types:
                if routing_type.display_name == type_name:
                    track.output_routing_type = routing_type
                    return
            self.logger.warning("Couldn't find output routing type: %s" % type_name)
        def track_get_output_routing_channel(track, _):
            return track.output_routing_channel.display_name,
        def track_set_output_routing_channel(track, params):
            channel_name = str(params[0])
            for channel in track.available_output_routing_channels:
                if channel.display_name == channel_name:
                    track.output_routing_channel = channel
                    return
            self.logger.warning("Couldn't find output routing channel: %s" % channel_name)
        def track_get_output_routings(track, _):
            return _routing_display_names(track.output_routings)
        def track_get_output_sub_routings(track, _):
            return _routing_display_names(track.output_sub_routings)
        def track_get_current_output_routing(track, _):
            return track.current_output_routing,
        def track_set_current_output_routing(track, params):
            routing_name = str(params[0])
            track.current_output_routing = routing_name
        def track_get_current_output_sub_routing(track, _):
            return track.current_output_sub_routing,
        def track_set_current_output_sub_routing(track, params):
            routing_name = str(params[0])
            track.current_output_sub_routing = routing_name

        #--------------------------------------------------------------------------------
        # Track: Input routing.
        #--------------------------------------------------------------------------------
        def track_get_available_input_routing_types(track, _):
            return _routing_display_names(track.available_input_routing_types)
        def track_get_available_input_routing_channels(track, _):
            return _routing_display_names(track.available_input_routing_channels)
        def track_get_input_routing_type(track, _):
            return track.input_routing_type.display_name,
        def track_set_input_routing_type(track, params):
            type_name = str(params[0])
            for routing_type in track.available_input_routing_types:
                if routing_type.display_name == type_name:
                    track.input_routing_type = routing_type
                    return
            self.logger.warning("Couldn't find input routing type: %s" % type_name)
        def track_get_input_routing_channel(track, _):
            return track.input_routing_channel.display_name,
        def track_set_input_routing_channel(track, params):
            channel_name = str(params[0])
            for channel in track.available_input_routing_channels:
                if channel.display_name == channel_name:
                    track.input_routing_channel = channel
                    return
            self.logger.warning("Couldn't find input routing channel: %s" % channel_name)
        def track_get_input_routings(track, _):
            return _routing_display_names(track.input_routings)
        def track_get_input_sub_routings(track, _):
            return _routing_display_names(track.input_sub_routings)
        def track_get_current_input_routing(track, _):
            return track.current_input_routing,
        def track_set_current_input_routing(track, params):
            routing_name = str(params[0])
            track.current_input_routing = routing_name
        def track_get_current_input_sub_routing(track, _):
            return track.current_input_sub_routing,
        def track_set_current_input_sub_routing(track, params):
            routing_name = str(params[0])
            track.current_input_sub_routing = routing_name

        # Add Handlers
        local_funcs = locals()
        for method, spec in methods.items():
            alias = spec.get("alias")
            caller = spec.get("caller")
            if not caller:
                continue
            if not alias and isinstance(caller, str):
                caller = local_funcs[caller]
                self.osc_server.add_handler("/live/track/%s" % method,
                                            create_track_callback(caller))
            else:
                if not alias:
                    caller = method
                self.osc_server.add_handler("/live/track/%s" % method,
                                            create_track_callback(self._call_method, caller))

        for prop, spec in properties.items():
            getter_func = spec.get("get")
            if getter_func in (True, 1):
                self.osc_server.add_handler("/live/track/get/%s" % prop,
                                            create_track_callback(self._get_property, prop))
            elif isinstance(getter_func, str):
                getter = local_funcs[getter_func]
                self.osc_server.add_handler("/live/track/get/%s" % prop,
                                            create_track_callback(getter))

            setter_func = spec.get("set")
            if setter_func in (True, 1):
                self.osc_server.add_handler("/live/track/set/%s" % prop,
                                            create_track_callback(self._set_property, prop))
            elif isinstance(setter_func, str):
                setter = local_funcs[setter_func]
                self.osc_server.add_handler("/live/track/set/%s" % prop,
                                            create_track_callback(setter))

            observable = spec.get("listen")
            if observable:
                self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                            create_track_callback(self._start_listen, prop, include_track_id=True))
                self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                            create_track_callback(self._stop_listen, prop, include_track_id=True))

        #--------------------------------------------------------------------------------
        # Mixer Properties
        # Volume, panning and send are properties of the track's mixer_device so
        # can't be formulated as normal callbacks that reference properties of track.
        #--------------------------------------------------------------------------------
        
        mixer_properties = {
            "volume":   {"get": 1, "set": 1, "listen": 1},
            "panning":  {"get": 1, "set": 1, "listen": 1},
            "send":     {"get": "track_get_send", "set": "track_set_send", "listen": 0},
            # New
            # "cue_volume":         {"get": 1, "set": 1, "listen": 1, "kind": "param"},  # main track only
            # "crossfader":         {"get": 1, "set": 1, "listen": 1, "kind": "param"},  # main track only
            # "song_tempo":         {"get": 1, "set": 1, "listen": 1, "kind": "param"},  # main track only
            "track_activator":    {"get": 1, "set": 1, "listen": 1, "kind": "param"},
            "left_split_stereo":  {"get": 1, "set": 1, "listen": 1, "kind": "param"},
            "right_split_stereo": {"get": 1, "set": 1, "listen": 1, "kind": "param"},
            "crossfade_assign":   {"get": 1, "set": 1, "listen": 1, "kind": "prop"},
            "panning_mode":       {"get": 1, "set": 1, "listen": 1, "kind": "prop"},
        }
        
        # Still need to fix these
        # Might want to find a better approach that unifies volume and sends
        def track_get_send(track, params: Tuple[Any] = ()):
            send_id, = params
            return send_id, track.mixer_device.sends[send_id].value

        def track_set_send(track, params: Tuple[Any] = ()):
            send_id, value = params
            track.mixer_device.sends[send_id].value = value
        
        local_funcs = locals()
        for prop, spec in mixer_properties.items():
            getter_func = spec.get("get")
            kind = spec.get("kind", "param")
            if getter_func in (True, 1):
                self.osc_server.add_handler("/live/track/get/%s" % prop,
                                            create_track_callback(self._get_mixer_property, prop, kind))
            elif isinstance(getter_func, str):
                getter = local_funcs[getter_func]
                self.osc_server.add_handler("/live/track/get/%s" % prop,
                                            create_track_callback(getter))

            setter_func = spec.get("set")
            if setter_func in (True, 1):
                self.osc_server.add_handler("/live/track/set/%s" % prop,
                                            create_track_callback(self._set_mixer_property, prop, kind))
            elif isinstance(setter_func, str):
                setter = local_funcs[setter_func]
                self.osc_server.add_handler("/live/track/set/%s" % prop,
                                            create_track_callback(setter))

            observable = spec.get("listen")
            if observable:
                self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                            create_track_callback(self._start_mixer_listen, prop, kind, include_track_id=True))
                self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                            create_track_callback(self._stop_mixer_listen, prop, kind, include_track_id=True))

    def _set_mixer_property(self, target, prop, kind: str, params: Tuple) -> None:
        value = params[0]
        self.logger.info("Setting property for %s: %s (new value %s)" % (self.class_identifier, prop, value))
        if kind == "param":
            parameter_object = getattr(target.mixer_device, prop)
            parameter_object.value = value
        else:
            setattr(target.mixer_device, prop, value)

    def _get_mixer_property(self, target, prop, kind: str, params: Optional[Tuple] = ()) -> Tuple[Any]:
        if kind == "param":
            value = getattr(target.mixer_device, prop).value
        else:
            value = getattr(target.mixer_device, prop)
        self.logger.info("Getting property for %s: %s = %s" % (self.class_identifier, prop, value))
        return (value,)

    def _start_mixer_listen(self, target, prop, kind: str, params: Optional[Tuple] = ()) -> None:
        if kind == "param":
            parameter_object = getattr(target.mixer_device, prop)
        else:
            parameter_object = target.mixer_device
        def property_changed_callback():
            value = parameter_object.value if kind == "param" else getattr(parameter_object, prop)
            self.logger.info("Property %s changed of %s %s: %s" % (prop, self.class_identifier, str(params), value))
            osc_address = "/live/%s/get/%s" % (self.class_identifier, prop)
            self.osc_server.send(osc_address, (*params, value,))

        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self._stop_mixer_listen(target, prop, params)

        self.logger.info("Adding listener for %s %s, property: %s" % (self.class_identifier, str(params), prop))

        if kind == "param":
            parameter_object.add_value_listener(property_changed_callback)
        else:
            add_listener_function = getattr(parameter_object, "add_%s_listener" % prop)
            add_listener_function(property_changed_callback)
        self.listener_functions[listener_key] = property_changed_callback
        #--------------------------------------------------------------------------------
        # Immediately send the current value
        #--------------------------------------------------------------------------------
        property_changed_callback()

    def _stop_mixer_listen(self, target, prop, kind: str, params: Optional[Tuple[Any]] = ()) -> None:
        if kind == "param":
            parameter_object = getattr(target.mixer_device, prop)
        else:
            parameter_object = target.mixer_device
        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self.logger.info("Removing listener for %s %s, property %s" % (self.class_identifier, str(params), prop))
            listener_function = self.listener_functions[listener_key]
            if kind == "param":
                parameter_object.remove_value_listener(listener_function)
            else:
                remove_listener_function = getattr(parameter_object, "remove_%s_listener" % prop)
                remove_listener_function(listener_function)
            del self.listener_functions[listener_key]
        else:
            self.logger.warning("No listener function found for property: %s (%s)" % (prop, str(params)))


class TrackViewHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "track_view"

    def init_api(self):
        def create_track_view_callback(func: Callable,
                                       *args,
                                       pass_track_index: bool = False):
            def view_callback(params: Tuple[Any]) -> Tuple:
                if params[0] == "*":
                    track_indices = list(range(len(self.song.tracks)))
                else:
                    track_indices = [int(params[0])]

                for track_index in track_indices:
                    track = self.song.tracks[track_index]
                    view = track.view
                    if pass_track_index:
                        rv = func(view, *args, tuple(params[0:]))
                    else:
                        rv = func(view, *args, tuple(params[1:]))
                    if rv is not None:
                        return (track_index, *rv)

            return view_callback

        methods = {
            # No methods yet
        }

        properties = {
            "canonical_parent":   {"get": 0, "set": 0, "listen": 0},  # Track object, not serializable
            "device_insert_mode": {"get": 1, "set": 0, "listen": 0},  # Get/Listen only per API
            "is_collapsed":       {"get": 1, "set": 1, "listen": 0},
            "selected_device":    {"get": 0, "set": 0, "listen": 0},  # Device object, not serializable
        }

        for method, spec in methods.items():
            caller = spec.get("caller")
            alias = spec.get("alias")
            if not caller:
                continue
            target = caller if alias else method
            self.osc_server.add_handler("/live/track/view/%s" % method,
                                        create_track_view_callback(self._call_method, target))

        for prop, spec in properties.items():
            getter_func = spec.get("get")
            if getter_func:
                self.osc_server.add_handler("/live/track/view/get/%s" % prop,
                                            create_track_view_callback(self._get_property, prop))

            setter_func = spec.get("set")
            if setter_func:
                self.osc_server.add_handler("/live/track/view/set/%s" % prop,
                                            create_track_view_callback(self._set_property, prop))

            listen_func = spec.get("listen")
            if listen_func:
                self.osc_server.add_handler("/live/track/view/start_listen/%s" % prop,
                                            create_track_view_callback(self._start_listen, prop, pass_track_index=True))
                self.osc_server.add_handler("/live/track/view/stop_listen/%s" % prop,
                                            create_track_view_callback(self._stop_listen, prop, pass_track_index=True))
