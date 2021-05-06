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

        def track_set_volume(track, params: Tuple[Any]):
            track.mixer_device.volume.value = params[0]
        def track_set_panning(track, params: Tuple[Any]):
            track.mixer_device.panning.value = params[0]
        def track_set_send(track, params: Tuple[Any]):
            send_id, value = params
            track.mixer_device.sends[send_id].value = value
        # TODO getters
        self.osc_server.add_handler("/live/track/set_property/volume", create_track_callback(track_set_volume))
        self.osc_server.add_handler("/live/track/set_property/panning", create_track_callback(track_set_panning))
        self.osc_server.add_handler("/live/track/set_property/send", create_track_callback(track_set_send))

        def track_get_clips(track, params: Tuple[Any]):
            clip_slots = track.clip_slots
            rv = []
            for clip_slot in clip_slots:
                clip = clip_slot.clip
                if clip:
                    rv.append(clip.name)
                else:
                    rv.append(None)
            return tuple(rv)
        self.osc_server.add_handler("/live/track/get_property/clips", create_track_callback(track_get_clips))
