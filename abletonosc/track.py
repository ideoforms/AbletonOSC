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
            "mute"
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
