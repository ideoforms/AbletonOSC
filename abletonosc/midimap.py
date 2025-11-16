from .handler import AbletonOSCHandler
from typing import Tuple, Any

class MidiMapHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "midimap"
        self.midi_map_handle = None

    def init_api(self):
        def make_midi_map(params: Tuple[Any] = ()):
            track_index = int(params[0])
            device_index = int(params[1])
            parameter_index = int(params[2])
            channel = int(params[3])
            cc = int(params[4])

            parameter = self.song.tracks[track_index].devices[device_index].parameters[parameter_index]
            self.manager.midi_mappings[(channel, cc)] = parameter
            
            self.manager.request_rebuild_midi_map()

        self.osc_server.add_handler("/live/midimap/map_cc", make_midi_map)