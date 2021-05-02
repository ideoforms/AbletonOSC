from ableton.v2.control_surface.components import ChannelStripComponent
from ableton.v2.base import liveobj_valid, listens

import logging
logger = logging.getLogger("abletonosc")

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
            logger.info(" - Invalid track")
            self._on_playing_slot_index_changed.subject = None
            self._on_volume_changed.subject = None
            self._on_panning_changed.subject = None

    @property
    def track_index(self):
        for index, track in enumerate(self.song.tracks):
            if track == self._track:
                return index

    @listens('value')
    def _on_volume_changed(self):
        logger.info("Volume changed: %s (track %d)" % (self._track.mixer_device.volume.value, self.track_index))

    @listens('value')
    def _on_panning_changed(self):
        logger.info("Panning changed: %s (track %d)" % self._track.mixer_device.panning.value, self.track_index)

    @listens('playing_slot_index')
    def _on_playing_slot_index_changed(self):
        logger.info("Slot index changed: %s (track %d)" % (self._track.playing_slot_index, self.track_index))