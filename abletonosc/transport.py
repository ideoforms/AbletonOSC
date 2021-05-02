from ableton.v2.control_surface.components import TransportComponent
from ableton.v2.base import listens, task

import logging
logger = logging.getLogger("abletonosc")

class CustomTransportComponent (TransportComponent):
    def __init__(self, manager: 'Manager'):
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
            self.manager.reload_imports()

        # Used to make an event happen in a listener
        # self._tasks.add(task.run(lambda: self.song.create_audio_track()))