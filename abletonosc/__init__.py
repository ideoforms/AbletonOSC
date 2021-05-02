import logging
logger = logging.getLogger("abletonosc")

from ableton.v2.control_surface.components import MixerComponent, SessionComponent

from .channel_strip import CustomChannelStripComponent
from .transport import CustomTransportComponent
from .osc_server import OSCServer

class CustomMixerComponent (MixerComponent):
    def __init__(self, manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager

class CustomSessionComponent (SessionComponent):
    pass