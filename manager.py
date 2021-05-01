from ableton.v2.control_surface import ControlSurface
from ableton.v2.control_surface.components import SessionRingComponent

from . import dyna
# from .pythonosc import dispatcher
# from .pythonosc import osc_server

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

        # disp = dispatcher.Dispatcher()
        # disp.map("/test", lambda: logger.info("test ok"))
        # self.server = osc_server.OSCUDPServer(("127.0.0.1", 12345), disp)
        # logger.info("Serving on {}".format(self.server.server_address))

        self.osc_handler = dyna.OSCHandler()
        self.schedule_message(1, self.refresh)

    def create_session(self):
        #--------------------------------------------------------------------------------
        # Needed when first registering components
        #--------------------------------------------------------------------------------
        with self.component_guard():
            self.transport = dyna.CustomTransportComponent(self)
            self.session_ring = SessionRingComponent(8, 8)
            self.session = dyna.CustomSessionComponent(session_ring=self.session_ring)
            self.mixer = dyna.CustomMixerComponent(self,
                                                   tracks_provider=self.session_ring,
                                                   channel_strip_component_type=dyna.CustomChannelStripComponent)

    def refresh(self):
        logger.info("Refresh...")
        # self.server._handle_request_noblock()
        self.osc_handler.process()
        self.schedule_message(1, self.refresh)

    def reload_imports(self):
        try:
            importlib.reload(dyna)
        except Exception as e:
            exc = traceback.format_exc()
            logging.warning(exc)
        logger.info("Reloaded code")

    def disconnect(self):
        self.show_message("Disconnecting...")
        self.osc_handler.shutdown()
        super().disconnect()
