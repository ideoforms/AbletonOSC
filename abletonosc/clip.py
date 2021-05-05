from typing import Tuple, Any
from .component import AbletonOSCComponent
import Live

class ClipComponent(AbletonOSCComponent):
    def init_api(self):
        def create_clip_callback(func, *args):
            def clip_callback(params: Tuple[Any]):
                track_index, clip_index = params[:2]
                track = self.song.tracks[track_index]
                clip = track.clip_slots[clip_index].clip
                return func(clip, *args, params[2:])

            return clip_callback

        methods = [
            "fire",
            "stop"
        ]
        properties_r = [
            "is_playing"
        ]
        properties_rw = [
            "color"
        ]

        for method in methods:
            self.osc_server.add_handler("/live/clip/%s" % method,
                                        create_clip_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/clip/get_property/%s" % prop,
                                        create_clip_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/clip/start_property_listen/%s" % prop,
                                        create_clip_callback(self._start_property_listen, prop))
            self.osc_server.add_handler("/live/clip/stop_property_listen/%s" % prop,
                                        create_clip_callback(self._stop_property_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/clip/set_property/%s" % prop,
                                        create_clip_callback(self._set_property, prop))

        def clip_add_new_note(clip, params: Tuple[Any]):
            start_time, duration, pitch, velocity, mute = params
            note = Live.Clip.MidiNoteSpecification(start_time=start_time,
                                                   duration=duration,
                                                   pitch=pitch,
                                                   velocity=velocity,
                                                   mute=mute)
            clip.add_new_notes((note,))

        self.osc_server.add_handler("/live/clip/add_new_note", create_clip_callback(clip_add_new_note))
