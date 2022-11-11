from functools import partial
from typing import Tuple, Any
from .handler import AbletonOSCHandler

class SongHandler(AbletonOSCHandler):
    def init_api(self):
        #--------------------------------------------------------------------------------
        # Init callbacks for Set: methods
        #--------------------------------------------------------------------------------
        for method in [
            "continue_playing",
            "create_audio_track",
            "create_midi_track",
            "create_return_track",
            "create_scene",
            "delete_return_track",
            "delete_scene",
            "delete_track",
            "duplicate_scene",
            "duplicate_track",
            "jump_by",
            "jump_to_prev_cue",
            "jump_to_next_cue",
            "redo",
            "start_playing",
            "stop_all_clips",
            "stop_playing",
            "tap_tempo",
            "trigger_session_record",
            "undo"
        ]:
            callback = partial(self._call_method, self.song, method)
            self.osc_server.add_handler("/live/song/%s" % method, callback)

        #--------------------------------------------------------------------------------
        # Init callbacks for Set: properties
        #--------------------------------------------------------------------------------
        properties_rw = [
            "arrangement_overdub",
            "back_to_arranger",
            "clip_trigger_quantization",
            "current_song_time",
            "groove_amount",
            "loop",
            "loop_length",
            "loop_start",
            "metronome",
            "midi_recording_quantization",
            "nudge_down",
            "nudge_up",
            "punch_in",
            "punch_out",
            "record_mode",
            "start_time",
            "tempo"
        ]
        properties_r = [
            "can_redo",
            "can_undo",
            "is_playing"
        ]

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/song/get/%s" % prop, partial(self._get_property, self.song, prop))
            self.osc_server.add_handler("/live/song/start_listen/%s" % prop, partial(self._start_listen, self.song, prop))
            self.osc_server.add_handler("/live/song/stop_listen/%s" % prop, partial(self._stop_listen, self.song, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/song/set/%s" % prop, partial(self._set_property, self.song, prop))

        def song_get_num_tracks(song, params: Tuple[Any] = ()):
            return len(song.tracks),
        def song_get_num_scenes(song, params: Tuple[Any] = ()):
            return len(song.scenes),

        self.osc_server.add_handler("/live/song/get/num_tracks", partial(song_get_num_tracks, self.song))
        self.osc_server.add_handler("/live/song/get/num_scenes", partial(song_get_num_scenes, self.song))

        def song_get_cue_points(song, params: Tuple[Any] = ()):
            cue_points = song.cue_points
            cue_point_pairs = [(cue_point.name, cue_point.time) for cue_point in cue_points]
            rv = (element for pair in cue_point_pairs for element in pair)
            return rv
        self.osc_server.add_handler("/live/song/get/cue_points", partial(song_get_cue_points, self.song))

        def song_jump_to_cue_point(song, params: Tuple[Any] = ()):
            cue_point_index = params[0]
            if isinstance(cue_point_index, str):
                for cue_point in song.cue_points:
                    if cue_point.name == cue_point_index:
                        cue_point.jump()
            elif isinstance(cue_point_index, int):
                cue_point = song.cue_points[cue_point_index]
                cue_point.jump()
        self.osc_server.add_handler("/live/song/cue_point/jump", partial(song_jump_to_cue_point, self.song))

        #--------------------------------------------------------------------------------
        # /live/song/beat listener
        #--------------------------------------------------------------------------------
        self.last_song_time = -1.0
        def song_time_changed():
            # If song has rewound or skipped to next beat, sent a /live/beat message
            if (self.song.current_song_time < self.last_song_time) or \
                    (int(self.song.current_song_time) > int(self.last_song_time)):
                self.osc_server.send("/live/song/beat", (int(self.song.current_song_time),))
            self.last_song_time = self.song.current_song_time
        self.song.add_current_song_time_listener(song_time_changed)
