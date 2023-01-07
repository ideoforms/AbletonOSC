from ableton.v2.control_surface import ControlSurface

from . import abletonosc

import importlib
import traceback
import logging
import os

logger = logging.getLogger("abletonosc")

def start_logging():
    module_path = os.path.dirname(os.path.realpath(__file__))
    log_dir = os.path.join(module_path, "logs")
    if not os.path.exists(log_dir):
        os.mkdir(log_dir, 0o755)
    log_path = os.path.join(log_dir, "abletonosc.log")
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

class Manager(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.handlers = []
        self.show_message("AbletonOSC: Listening for OSC on port %d" % abletonosc.OSC_LISTEN_PORT)

        self.osc_server = abletonosc.OSCServer()
        self.schedule_message(0, self.tick)

        self.init_api()

        class LiveOSCErrorLogHandler(logging.StreamHandler):
            def emit(handler, record):
                message = record.getMessage()
                message = message[message.index(":") + 2:]
                try:
                    self.osc_server.send("/live/error", (message,))
                except OSError:
                    # If the connection is dead, silently ignore errors as there's not much more we can do
                    pass
        self.live_osc_error_handler = LiveOSCErrorLogHandler()
        self.live_osc_error_handler.setLevel(logging.ERROR)
        logger.addHandler(self.live_osc_error_handler)

    def init_api(self):
        def test_callback(params):
            self.show_message("Received OSC OK")
            self.osc_server.send("/live/test", ("ok",))
        def reload_callback(params):
            self.reload_imports()

        self.osc_server.add_handler("/live/test", test_callback)
        self.osc_server.add_handler("/live/reload", reload_callback)

        with self.component_guard():
            self.handlers = [
                abletonosc.SongHandler(self),
                abletonosc.ApplicationHandler(self),
                abletonosc.ClipHandler(self),
                abletonosc.ClipSlotHandler(self),
                abletonosc.TrackHandler(self),
                abletonosc.DeviceHandler(self)
            ]

    def clear_api(self):
        self.osc_server.clear_handlers()
        for handler in self.handlers:
            handler.clear_api()

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
            importlib.reload(abletonosc.application)
            importlib.reload(abletonosc.clip)
            importlib.reload(abletonosc.clip_slot)
            importlib.reload(abletonosc.device)
            importlib.reload(abletonosc.handler)
            importlib.reload(abletonosc.osc_server)
            importlib.reload(abletonosc.song)
            importlib.reload(abletonosc.track)
            importlib.reload(abletonosc)
        except Exception as e:
            exc = traceback.format_exc()
            logging.warning(exc)

        if self.handlers:
            self.clear_api()
            self.init_api()
        logger.info("Reloaded code")

    def disconnect(self):
        self.show_message("Disconnecting...")
        logger.info("Disconnecting...")
        self.osc_server.shutdown()
        super().disconnect()

start_logging()
