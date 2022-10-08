from functools import partial
from typing import Tuple, Any
from .handler import AbletonOSCHandler

class SongHandler(AbletonOSCHandler):
    def init_api(self):
        #--------------------------------------------------------------------------------
        # Init callbacks for Set: methods
        #--------------------------------------------------------------------------------
        for method in [
            "start_playing",
            "stop_playing",
            "continue_playing",
            "stop_all_clips",
            "create_audio_track",
            "create_midi_track",
            "create_return_track",
            "create_scene",
            "jump_by",
            "jump_to_prev_cue",
            "jump_to_next_cue",
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
            "tempo"
        ]
        properties_r = [
            "is_playing"
        ]

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/song/get/%s" % prop, partial(self._get, self.song, prop))
            self.osc_server.add_handler("/live/song/start_listen/%s" % prop, partial(self._start_listen, self.song, prop))
            self.osc_server.add_handler("/live/song/stop_listen/%s" % prop, partial(self._stop_listen, self.song, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/song/set/%s" % prop, partial(self._set, self.song, prop))

        def song_get_num_tracks(song, params: Tuple[Any] = ()):
            return len(song.tracks),
        def song_get_num_scenes(song, params: Tuple[Any] = ()):
            return len(song.scenes),

        # TODO num_tracks listener
        self.osc_server.add_handler("/live/song/get/num_tracks", partial(song_get_num_tracks, self.song))
        self.osc_server.add_handler("/live/song/get/num_scenes", partial(song_get_num_scenes, self.song))

        self.last_song_time = -1.0

        def song_time_changed():
            # If song has rewound or skipped to next beat, sent a /live/beat message
            if (self.song.current_song_time < self.last_song_time) or \
                    (int(self.song.current_song_time) > int(self.last_song_time)):
                self.osc_server.send("/live/song/beat", (int(self.song.current_song_time),))
            self.last_song_time = self.song.current_song_time
        self.song.add_current_song_time_listener(song_time_changed)
