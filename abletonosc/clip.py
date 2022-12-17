from typing import Tuple, Callable, Any, Optional
from .handler import AbletonOSCHandler
import Live

class ClipHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "clip"

    def init_api(self):
        def create_clip_callback(func, *args, pass_clip_index=False):
            """
            Creates a callback that expects the following set of arguments:
              (track_index, clip_index, *args)

            The callback then extracts the relevant `Clip` object from the current Song,
            and calls `func` with this `Clip` object plus any additional *args.

            pass_clip_index is a bit of an ugly hack, although seems like the lesser of
            evils for scenarios where the track/clip index is needed (as a clip is unable
            to query its own index). Other alternatives include _always_ passing track/clip
            index to the callback, but this adds arg clutter to every single callback.
            """
            def clip_callback(params: Tuple[Any]) -> Tuple:
                #--------------------------------------------------------------------------------
                # Cast to int to support clients such as TouchOSC that, by default, pass all
                # numeric arguments as float.
                #--------------------------------------------------------------------------------
                track_index, clip_index = int(params[0]), int(params[1])
                track = self.song.tracks[track_index]
                clip = track.clip_slots[clip_index].clip
                if pass_clip_index:
                    rv = func((track_index, clip_index), *args, params[2:])
                else:
                    rv = func(clip, *args, params[2:])

                if rv:
                    return (track_index, clip_index, *rv)

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
            "is_recording",
            "length",
            "playing_position"
        ]
        properties_rw = [
            "color",
            "gain",
            "name",
            "pitch_coarse",
            "pitch_fine",
            "looping",
            "warping"
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
            return tuple(item for sublist in notes for item in sublist)

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

        # TODO: tidy up and generalise this
        self.clip_listeners = {}
        def clip_add_playing_position_listener(track_clip_index, params: Tuple[Any] = ()):
            track_index, clip_index = track_clip_index
            clip = self.song.tracks[track_index].clip_slots[clip_index].clip

            def playing_position_changed_callback():
                osc_address = "/live/clip/get/playing_position"
                self.osc_server.send(osc_address, (track_index, clip_index, clip.playing_position))

            clip_remove_playing_position_listener(track_clip_index)
            clip.add_playing_position_listener(playing_position_changed_callback)
            self.clip_listeners[track_clip_index] = playing_position_changed_callback

        def clip_remove_playing_position_listener(track_clip_index, params: Tuple[Any] = ()):
            track_index, clip_index = track_clip_index
            clip = self.song.tracks[track_index].clip_slots[clip_index].clip

            if track_clip_index in self.clip_listeners.keys():
                clip.remove_playing_position_listener(self.clip_listeners[track_clip_index])
                del self.clip_listeners[track_clip_index]

        self.osc_server.add_handler("/live/clip/start_listen/playing_position",
                                    create_clip_callback(clip_add_playing_position_listener, pass_clip_index=True))
        self.osc_server.add_handler("/live/clip/stop_listen/playing_position",
                                    create_clip_callback(clip_remove_playing_position_listener, pass_clip_index=True))
