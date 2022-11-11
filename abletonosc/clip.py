from typing import Tuple, Callable, Any
from .handler import AbletonOSCHandler
import Live

class ClipHandler(AbletonOSCHandler):
    def init_api(self):
        def create_clip_callback(func, *args):
            """
            Creates a callback that expects the following set of arguments:
              (track_index, clip_index, *args)

            The callback then extracts the relevant `Clip` object from the current Song,
            and calls `func` with this `Clip` object plus any additional *args.
            """
            def clip_callback(params: Tuple[Any]) -> Callable:
                track_index, clip_index = params[:2]
                track = self.song.tracks[track_index]
                clip = track.clip_slots[clip_index].clip
                return func(clip, *args, params[2:])

            return clip_callback

        methods = [
            "fire",
            "stop",
            "remove_notes_by_id"
        ]
        properties_r = [
            "file_path",
            "gain_display_string",
            "is_midi_clip",
            "is_audio_clip",
            "is_playing",
            "is_recording"
        ]
        properties_rw = [
            "color",
            "gain",
            "name",
            "pitch_coarse",
            "pitch_fine",
            "looping"
        ]

        for method in methods:
            self.osc_server.add_handler("/live/clip/%s" % method,
                                        create_clip_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/clip/get/%s" % prop,
                                        create_clip_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/clip/start_listen/%s" % prop,
                                        create_clip_callback(self._start_listen, prop))
            self.osc_server.add_handler("/live/clip/stop_listen/%s" % prop,
                                        create_clip_callback(self._stop_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/clip/set/%s" % prop,
                                        create_clip_callback(self._set_property, prop))

        def clip_get_notes(clip, params: Tuple[Any] = ()):
            notes = clip.get_notes(0, 0, clip.length, 127)
            return (item for sublist in notes for item in sublist)

        def clip_add_notes(clip, params: Tuple[Any] = ()):
            notes = []
            for offset in range(0, len(params), 5):
                pitch, start_time, duration, velocity, mute = params[offset:offset+5]
                note = Live.Clip.MidiNoteSpecification(start_time=start_time,
                                                       duration=duration,
                                                       pitch=pitch,
                                                       velocity=velocity,
                                                       mute=mute)
                notes.append(note)
            clip.add_new_notes(tuple(notes))

        def clip_remove_notes(clip, params: Tuple[Any] = ()):
            start_pitch, pitch_span, start_time, time_span = params
            clip.remove_notes_extended(start_pitch, pitch_span, start_time, time_span)

        self.osc_server.add_handler("/live/clip/get/notes", create_clip_callback(clip_get_notes))
        self.osc_server.add_handler("/live/clip/add/notes", create_clip_callback(clip_add_notes))
        self.osc_server.add_handler("/live/clip/remove/notes", create_clip_callback(clip_remove_notes))

