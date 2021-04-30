from ableton.v2.control_surface import ControlSurface
from ableton.v2.control_surface.components import TransportComponent, MixerComponent, ChannelStripComponent, SessionRingComponent, SessionComponent
from ableton.v2.base.event import listens
from ableton.v2.base import liveobj_valid

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

class CustomTransportComponent (TransportComponent):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self._on_tempo_changed.subject = self.song
        self._on_playing_changed.subject = self.song

    @listens('tempo')
    def _on_tempo_changed(self):
        logger.info("Tempo changed (%.1f)" % self.song.tempo)

    @listens('is_playing')
    def _on_playing_changed(self):
        if self.song.is_playing:
            self.manager.reload()

class CustomMixerComponent (MixerComponent):
    def __init__(self, manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager

class CustomChannelStripComponent (ChannelStripComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Instantiated ChannelStripComponent")

    def set_track(self, track):
        super().set_track(track)
        logger.info(" - Set track %s" % track)
        if liveobj_valid(track):
            self._on_playing_slot_index_changed.subject = track
            self._on_volume_changed.subject = track.mixer_device.volume
            self._on_panning_changed.subject = track.mixer_device.panning
        else:
            logger.info(" - Invalid")
            self._on_playing_slot_index_changed.subject = None
            self._on_volume_changed.subject = None
            self._on_panning_changed.subject = None

    @listens('value')
    def _on_volume_changed(self):
        logger.info("Volume changed: %s" % self._track.mixer_device.volume.value)

    @listens('value')
    def _on_panning_changed(self):
        logger.info("Panning changed: %s" % self._track.mixer_device.panning.value)

    @listens('playing_slot_index')
    def _on_playing_slot_index_changed(self):
        logger.info("Slot index changed: %s" % self._track.playing_slot_index)

class CustomSessionComponent (SessionComponent):
    pass

class Tester (ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.show_message("Loaded LiveOSC")

        #--------------------------------------------------------------------------------
        # Needed when first registering components
        #--------------------------------------------------------------------------------
        with self.component_guard():
            self.transport = CustomTransportComponent(self)
            self.session_ring = SessionRingComponent()
            self.session = CustomSessionComponent(session_ring=self.session_ring)
            self.mixer = CustomMixerComponent(self,
                                              tracks_provider=self.session_ring,
                                              channel_strip_component_type=CustomChannelStripComponent)

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
