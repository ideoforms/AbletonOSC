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
            "jump_by"
        ]:
            callback = partial(self._call_method, self.song, method)
            self.osc_server.add_handler("/live/set/%s" % method, callback)

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
            self.osc_server.add_handler("/live/set/get_property/%s" % prop, partial(self._get_property, self.song, prop))
            self.osc_server.add_handler("/live/set/start_property_listen/%s" % prop, partial(self._start_property_listen, self.song, prop))
            self.osc_server.add_handler("/live/set/stop_property_listen/%s" % prop, partial(self._stop_property_listen, self.song, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/set/set_property/%s" % prop, partial(self._set_property, self.song, prop))

        def song_get_num_tracks(song, params: Tuple[Any] = ()):
            return len(song.tracks),
        # TODO num_tracks listener
        self.osc_server.add_handler("/live/set/get_property/num_tracks", partial(song_get_num_tracks, self.song))
