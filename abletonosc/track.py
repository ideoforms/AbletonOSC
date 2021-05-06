from typing import Tuple, Any
from .component import AbletonOSCComponent

class TrackComponent(AbletonOSCComponent):
    def init_api(self):
        def create_track_callback(func, *args):
            def track_callback(params: Tuple[Any]):
                track_index = params[0]
                track = self.song.tracks[track_index]
                return func(track, *args, params[1:])

            return track_callback

        methods = [
            "stop_all_clips"
        ]
        properties_r = [
        ]
        properties_rw = [
            "color",
            "mute",
            "solo"
        ]

        for method in methods:
            self.osc_server.add_handler("/live/track/%s" % method,
                                        create_track_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/track/get_property/%s" % prop,
                                        create_track_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/track/start_property_listen/%s" % prop,
                                        create_track_callback(self._start_property_listen, prop))
            self.osc_server.add_handler("/live/track/stop_property_listen/%s" % prop,
                                        create_track_callback(self._stop_property_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/track/set_property/%s" % prop,
                                        create_track_callback(self._set_property, prop))

        def track_get_volume(track, params: Tuple[Any] = ()):
            return track.mixer_device.volume.value

        def track_set_volume(track, params: Tuple[Any] = ()):
            track.mixer_device.volume.value = params[0]

        def track_get_panning(track, params: Tuple[Any] = ()):
            return track.mixer_device.panning.value

        def track_set_panning(track, params: Tuple[Any] = ()):
            track.mixer_device.panning.value = params[0]

        def track_get_send(track, params: Tuple[Any] = ()):
            return track.mixer_device.sends[params[0]]

        def track_set_send(track, params: Tuple[Any] = ()):
            send_id, value = params
            track.mixer_device.sends[send_id].value = value

        # For some reason, volume/panning listeners don't seem to be exposed in the API
        self.osc_server.add_handler("/live/track/get_property/volume", create_track_callback(track_get_volume))
        self.osc_server.add_handler("/live/track/set_property/volume", create_track_callback(track_set_volume))
        self.osc_server.add_handler("/live/track/get_property/panning", create_track_callback(track_get_panning))
        self.osc_server.add_handler("/live/track/set_property/panning", create_track_callback(track_set_panning))
        self.osc_server.add_handler("/live/track/get_property/send", create_track_callback(track_get_send))
        self.osc_server.add_handler("/live/track/set_property/send", create_track_callback(track_set_send))

        def track_get_clip_names(track, params: Tuple[Any]):
            return tuple(clip_slot.clip.name if clip_slot.clip else None for clip_slot in track.clip_slots)
        def track_get_clip_lengths(track, params: Tuple[Any]):
            return tuple(clip_slot.clip.length if clip_slot.clip else None for clip_slot in track.clip_slots)

        """
        Returns a list of clip properties, or Nil if clip is empty
        """
        self.osc_server.add_handler("/live/track/get_property/clips/name", create_track_callback(track_get_clip_names))
        self.osc_server.add_handler("/live/track/get_property/clips/length", create_track_callback(track_get_clip_lengths))

        def track_get_num_devices(track, params: Tuple[Any]):
            return len(track.devices),
        def track_get_device_names(track, params: Tuple[Any]):
            return tuple(device.name for device in track.devices)
        def track_get_device_types(track, params: Tuple[Any]):
            return tuple(device.type for device in track.devices)
        def track_get_device_class_names(track, params: Tuple[Any]):
            return tuple(device.class_name for device in track.devices)
        def track_get_device_can_have_chains(track, params: Tuple[Any]):
            return tuple(device.can_have_chains for device in track.devices)

        """
         - name: the device's human-readable name
         - type: 0 = audio_effect, 1 = instrument, 2 = midi_effect
         - class_name: e.g. Operator, Reverb, AuPluginDevice, PluginDevice, InstrumentGroupDevice
        """
        self.osc_server.add_handler("/live/track/get_property/num_devices", create_track_callback(track_get_num_devices))
        self.osc_server.add_handler("/live/track/get_property/devices/name", create_track_callback(track_get_device_names))
        self.osc_server.add_handler("/live/track/get_property/devices/type", create_track_callback(track_get_device_types))
        self.osc_server.add_handler("/live/track/get_property/devices/class_name", create_track_callback(track_get_device_class_names))
        self.osc_server.add_handler("/live/track/get_property/devices/can_have_chains", create_track_callback(track_get_device_can_have_chains))