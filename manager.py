from ableton.v2.control_surface import ControlSurface

from . import abletonosc

import importlib
import traceback
import logging

logger = logging.getLogger("abletonosc")
file_handler = logging.FileHandler('/tmp/abletonosc.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Manager(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.reload_imports()
        self.show_message("Loaded AbletonOSC")

        self.osc_server = abletonosc.OSCServer()
        self.schedule_message(0, self.tick)

        self.init_api()

    def init_api(self):
        self.osc_server.add_handler("/live/test", lambda _, params: self.show_message("Received OSC OK"))

        with self.component_guard():
            self.song_component = abletonosc.SongComponent(self)
            self.application_component = abletonosc.ApplicationComponent(self)
            self.clip_component = abletonosc.ClipComponent(self)
            self.clip_slot_component = abletonosc.ClipSlotComponent(self)
            self.track_component = abletonosc.TrackComponent(self)

    def tick(self):
        """
        Called once per 100ms "tick".
        Live's embedded Python implementation does not appear to support threading,
        and beachballs when a thread is started. Instead, this approach allows long-running
        processes such as the OSC server to perform operations.
        """
        logger.debug("Tick...")
        self.osc_server.process()
        self.schedule_message(1, self.tick)

    def reload_imports(self):
        try:
            importlib.reload(abletonosc)
        except Exception as e:
            exc = traceback.format_exc()
            logging.warning(exc)
        logger.info("Reloaded code")

    def disconnect(self):
        self.show_message("Disconnecting...")
        self.osc_server.shutdown()
        super().disconnect()
