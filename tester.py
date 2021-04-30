from ableton.v2.control_surface import ControlSurface, Component
from ableton.v2.base.event import listens

from . import dyna
import importlib
import traceback
import logging

logger = logging.getLogger()
file_handler = logging.FileHandler('/tmp/liveosc.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class TransportState(Component):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self._on_tempo_changed.subject = self.song
        self._on_playing_changed.subject = self.song

    @listens('tempo')
    def _on_tempo_changed(self):
        logging.info("Tempo changed (%.1f)" % self.song.tempo)

    @listens('is_playing')
    def _on_playing_changed(self):
        if self.song.is_playing:
            self.manager.reload()

class Tester (ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.show_message("Loaded LiveOSC")

        #--------------------------------------------------------------------------------
        # Needed when first registering components
        #--------------------------------------------------------------------------------
        with self.component_guard():
            self.transport_state = TransportState(self)

    def reload(self):
        try:
            importlib.reload(dyna)
        except Exception as e:
            exc = traceback.format_exc()
            logging.warning(exc)
        d = dyna.DynamicClass()
        logger.info("Reloaded code (%s)" % d.foo())

    def disconnect(self):
        self.show_message("Disconnecting...")
        super().disconnect()
