from ableton.v2.control_surface.component import Component

class AbletonOSCComponent(Component):
    def __init__(self, manager):
        super().__init__()

        self.manager = manager
        self.osc_server = self.manager.osc_server
        self.init_api()
        self.listener_functions = {}

    def init_api(self):
        pass