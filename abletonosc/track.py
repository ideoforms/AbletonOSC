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

        methods = [
            "delete_device",
            "stop_all_clips"
        ]
        properties_r = [
            "can_be_armed",
            "fired_slot_index",
            "has_audio_input",
            "has_audio_output",
            "has_midi_input",
            "has_midi_output",
            "is_foldable",
            "is_grouped",
            "is_visible",
            "output_meter_level",
            "output_meter_left",
            "output_meter_right",
            "playing_slot_index",
        ]
        properties_rw = [
            "arm",
            "color",
            "color_index",
            "current_monitoring_state",
            "fold_state",
            "mute",
            "solo",
            "name"
        ]

        for method in methods:
            self.osc_server.add_handler("/live/track/%s" % method,
                                        create_track_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/track/get/%s" % prop,
                                        create_track_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                        create_track_callback(self._start_listen, prop, include_track_id=True))
            self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                        create_track_callback(self._stop_listen, prop, include_track_id=True))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/track/set/%s" % prop,
                                        create_track_callback(self._set_property, prop))

        #--------------------------------------------------------------------------------
        # Volume, panning and send are properties of the track's mixer_device so
        # can't be formulated as normal callbacks that reference properties of track.
        #--------------------------------------------------------------------------------
        mixer_properties_rw = ["volume", "panning"]
        for prop in mixer_properties_rw:
            self.osc_server.add_handler("/live/track/get/%s" % prop,
                                        create_track_callback(self._get_mixer_property, prop))
            self.osc_server.add_handler("/live/track/set/%s" % prop,
                                        create_track_callback(self._set_mixer_property, prop))
            self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                        create_track_callback(self._start_mixer_listen, prop, include_track_id=True))
            self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                        create_track_callback(self._stop_mixer_listen, prop, include_track_id=True))

        # Still need to fix these
        # Might want to find a better approach that unifies volume and sends
        def track_get_send(track, params: Tuple[Any] = ()):
            send_id, = params
            return track.mixer_device.sends[send_id].value,

        def track_set_send(track, params: Tuple[Any] = ()):
            send_id, value = params
            track.mixer_device.sends[send_id].value = value

        self.osc_server.add_handler("/live/track/get/send", create_track_callback(track_get_send))
        self.osc_server.add_handler("/live/track/set/send", create_track_callback(track_set_send))

        def track_delete_clip(track, params: Tuple[Any]):
            clip_index, = params
            track.clip_slots[clip_index].delete_clip()

        self.osc_server.add_handler("/live/track/delete_clip", create_track_callback(track_delete_clip))

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

        """
        Returns a list of clip properties, or Nil if clip is empty
        """
        self.osc_server.add_handler("/live/track/get/clips/name", create_track_callback(track_get_clip_names))
        self.osc_server.add_handler("/live/track/get/clips/length", create_track_callback(track_get_clip_lengths))
        self.osc_server.add_handler("/live/track/get/clips/color", create_track_callback(track_get_clip_colors))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/name", create_track_callback(track_get_arrangement_clip_names))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/length", create_track_callback(track_get_arrangement_clip_lengths))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/start_time", create_track_callback(track_get_arrangement_clip_start_times))

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

        """
         - name: the device's human-readable name
         - type: 0 = audio_effect, 1 = instrument, 2 = midi_effect
         - class_name: e.g. Operator, Reverb, AuPluginDevice, PluginDevice, InstrumentGroupDevice
        """
        self.osc_server.add_handler("/live/track/get/num_devices", create_track_callback(track_get_num_devices))
        self.osc_server.add_handler("/live/track/get/devices/name", create_track_callback(track_get_device_names))
        self.osc_server.add_handler("/live/track/get/devices/type", create_track_callback(track_get_device_types))
        self.osc_server.add_handler("/live/track/get/devices/class_name", create_track_callback(track_get_device_class_names))
        self.osc_server.add_handler("/live/track/get/devices/can_have_chains", create_track_callback(track_get_device_can_have_chains))

        #--------------------------------------------------------------------------------
        # Track: Output routing.
        # An output route has a type (e.g. "Ext. Out") and a channel (e.g. "1/2").
        # Since Live 10, both of these need to be set by reference to the appropriate
        # item in the available_output_routing_types vector.
        #--------------------------------------------------------------------------------
        def track_get_available_output_routing_types(track, _):
            return tuple([routing_type.display_name for routing_type in track.available_output_routing_types])
        def track_get_available_output_routing_channels(track, _):
            return tuple([routing_channel.display_name for routing_channel in track.available_output_routing_channels])
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

        self.osc_server.add_handler("/live/track/get/available_output_routing_types", create_track_callback(track_get_available_output_routing_types))
        self.osc_server.add_handler("/live/track/get/available_output_routing_channels", create_track_callback(track_get_available_output_routing_channels))
        self.osc_server.add_handler("/live/track/get/output_routing_type", create_track_callback(track_get_output_routing_type))
        self.osc_server.add_handler("/live/track/set/output_routing_type", create_track_callback(track_set_output_routing_type))
        self.osc_server.add_handler("/live/track/get/output_routing_channel", create_track_callback(track_get_output_routing_channel))
        self.osc_server.add_handler("/live/track/set/output_routing_channel", create_track_callback(track_set_output_routing_channel))

        #--------------------------------------------------------------------------------
        # Track: Input routing.
        #--------------------------------------------------------------------------------
        def track_get_available_input_routing_types(track, _):
            return tuple([routing_type.display_name for routing_type in track.available_input_routing_types])
        def track_get_available_input_routing_channels(track, _):
            return tuple([routing_channel.display_name for routing_channel in track.available_input_routing_channels])
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

        self.osc_server.add_handler("/live/track/get/available_input_routing_types", create_track_callback(track_get_available_input_routing_types))
        self.osc_server.add_handler("/live/track/get/available_input_routing_channels", create_track_callback(track_get_available_input_routing_channels))
        self.osc_server.add_handler("/live/track/get/input_routing_type", create_track_callback(track_get_input_routing_type))
        self.osc_server.add_handler("/live/track/set/input_routing_type", create_track_callback(track_set_input_routing_type))
        self.osc_server.add_handler("/live/track/get/input_routing_channel", create_track_callback(track_get_input_routing_channel))
        self.osc_server.add_handler("/live/track/set/input_routing_channel", create_track_callback(track_set_input_routing_channel))

    def _set_mixer_property(self, target, prop, params: Tuple) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        self.logger.info("Setting property for %s: %s (new value %s)" % (self.class_identifier, prop, params[0]))
        parameter_object.value = params[0]

    def _get_mixer_property(self, target, prop, params: Optional[Tuple] = ()) -> Tuple[Any]:
        parameter_object = getattr(target.mixer_device, prop)
        self.logger.info("Getting property for %s: %s = %s" % (self.class_identifier, prop, parameter_object.value))
        return parameter_object.value,

    def _start_mixer_listen(self, target, prop, params: Optional[Tuple] = ()) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        def property_changed_callback():
            value = parameter_object.value
            self.logger.info("Property %s changed of %s %s: %s" % (prop, self.class_identifier, str(params), value))
            osc_address = "/live/%s/get/%s" % (self.class_identifier, prop)
            self.osc_server.send(osc_address, (*params, value,))

        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self._stop_mixer_listen(target, prop, params)

        self.logger.info("Adding listener for %s %s, property: %s" % (self.class_identifier, str(params), prop))

        parameter_object.add_value_listener(property_changed_callback)
        self.listener_functions[listener_key] = property_changed_callback
        #--------------------------------------------------------------------------------
        # Immediately send the current value
        #--------------------------------------------------------------------------------
        property_changed_callback()

    def _stop_mixer_listen(self, target, prop, params: Optional[Tuple[Any]] = ()) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self.logger.info("Removing listener for %s %s, property %s" % (self.class_identifier, str(params), prop))
            listener_function = self.listener_functions[listener_key]
            parameter_object.remove_value_listener(listener_function)
            del self.listener_functions[listener_key]
        else:
            self.logger.warning("No listener function found for property: %s (%s)" % (prop, str(params)))
