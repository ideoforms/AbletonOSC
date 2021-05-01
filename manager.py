from ableton.v2.control_surface import ControlSurface
from ableton.v2.control_surface.components import SessionRingComponent

from . import dyna

import importlib
import traceback
import logging

logger = logging.getLogger("liveosc")
file_handler = logging.FileHandler('/tmp/liveosc.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Manager (ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.reload_imports()
        self.show_message("Loaded LiveOSC")
        self.create_session()

        self.osc_server = dyna.OSCServer()
        self.schedule_message(0, self.tick)

    def create_session(self):
        #--------------------------------------------------------------------------------
        # Needed when first registering components
        #--------------------------------------------------------------------------------
        with self.component_guard():
            self.transport = dyna.CustomTransportComponent(self)
            self.session_ring = SessionRingComponent()
            self.session = dyna.CustomSessionComponent(session_ring=self.session_ring)
            self.mixer = dyna.CustomMixerComponent(self,
                                                   tracks_provider=self.session_ring,
                                                   channel_strip_component_type=dyna.CustomChannelStripComponent)

        self.song.add_tempo_listener(self.on_tempo_changed)

    def on_tempo_changed(self):
        self.show_message("Tempo: %.1f" % self.song.tempo)

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
