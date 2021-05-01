from ableton.v2.control_surface import ControlSurface

from . import dyna

import importlib
import traceback
import functools
import logging

logger = logging.getLogger("liveosc")
file_handler = logging.FileHandler('/tmp/liveosc.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Manager(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.reload_imports()
        self.show_message("Loaded LiveOSC")

        self.osc_server = dyna.OSCServer()
        self.schedule_message(0, self.tick)

        self.create_session()

    def create_session(self):
        self.osc_server.add_handler("/live/test", lambda _, params: self.show_message("Received OSC OK"))

        set_properties = [
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
            "record_mode"
        ]
        for property in set_properties:
            address = "/live/set/%s" % property
            def set_property(prop, address, params):
                setattr(self.song, prop, params[0])
            callback = functools.partial(set_property, property)
            self.osc_server.add_handler(address, callback)

        set_methods = [
            "start_playing",
            "stop_playing",
            "stop_all_clips",
            "create_audio_track",
            "create_midi_track"
        ]
        for method in set_methods:
            address = "/live/set/%s" % method
            def call_method(_method, address, params):
                getattr(self.song, _method)()
            callback = functools.partial(call_method, method)
            self.osc_server.add_handler(address, callback)

        self.song.add_tempo_listener(self.on_tempo_changed)

    def on_tempo_changed(self):
        self.show_message("Tempo: %.1f" % self.song.tempo)
        self.osc_server.send("/live/tempo", (self.song.tempo,))

    def tick(self):
        """
        Called once per 100ms "tick".
        Live's embedded Python implementation does not appear to support threading,
        and beachballs when a thread is started. Instead, this approach allows long-running
        processes such as the OSC server to perform operations.
        """
        logger.info("Tick...")
        self.osc_server.process()
        self.schedule_message(1, self.tick)

    def reload_imports(self):
        try:
            importlib.reload(dyna)
        except Exception as e:
            exc = traceback.format_exc()
            logging.warning(exc)
        logger.info("Reloaded code")

    def disconnect(self):
        self.show_message("Disconnecting...")
        self.osc_server.shutdown()
        super().disconnect()
