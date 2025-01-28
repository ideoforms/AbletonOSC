from .handler import AbletonOSCHandler
from functools import partial
from typing import Tuple, Any

class SceneHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "scene"

    def init_api(self):
        # TODO: Needs unit tests

        def create_scene_callback(func, *args, include_ids: bool = False):
            def scene_callback(params: Tuple[Any]):
                scene_index = int(params[0])
                scene = self.song.scenes[scene_index]
                if (include_ids):
                    rv = func(scene, *args, params[0:])
                else:
                    rv = func(scene, *args, params[1:])

                if rv is not None:
                    return (scene_index, *rv)

            return scene_callback

        methods = [
            "fire",
        ]
        properties_r = [
        ]
        properties_rw = [
        ]

        for method in methods:
            self.osc_server.add_handler("/live/scene/%s" % method, create_scene_callback(self._call_method, method))
