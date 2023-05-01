from functools import partial
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler

class ViewHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "view"

    def init_api(self):
        def get_selected_scene(params: Optional[Tuple] = ()):
            return (list(self.song.scenes).index(self.song.view.selected_scene),)

        def get_selected_track(params: Optional[Tuple] = ()):
            tracks = list(self.song.tracks + [self.song.master_track])
            return (tracks.index(self.song.view.selected_track),)

        def get_selected_clip(params: Optional[Tuple] = ()):
            return (get_selected_track()[0], get_selected_scene()[0])

        def set_selected_scene(params: Optional[Tuple] = ()):
            index = params[0]
            if(index >= 0 and index < len(self.song.scenes)):
                scene = self.song.scenes[index]
                self.song.view.selected_scene = scene

        def set_selected_track(params: Optional[Tuple] = ()):
            index = params[0]
            tracks = list(self.song.tracks + [ self.song.master_track ])
            if(index >= 0 and index < len(tracks)):
                track = tracks[index]
                self.song.view.selected_track = track

        def set_selected_clip(params: Optional[Tuple] = ()):
            set_selected_track((params[0],))
            set_selected_scene((params[1],))

        self.osc_server.add_handler("/live/view/get/selected_scene", get_selected_scene)
        self.osc_server.add_handler("/live/view/get/selected_track", get_selected_track)
        self.osc_server.add_handler("/live/view/get/selected_clip", get_selected_clip)

        self.osc_server.add_handler("/live/view/set/selected_scene", set_selected_scene)
        self.osc_server.add_handler("/live/view/set/selected_track", set_selected_track)
        self.osc_server.add_handler("/live/view/set/selected_clip", set_selected_clip)