import Live
from typing import Tuple
from .component import AbletonOSCComponent

class ApplicationComponent(AbletonOSCComponent):
    def init_api(self):
        #--------------------------------------------------------------------------------
        # Generic callbacks
        #--------------------------------------------------------------------------------
        def get_version(_) -> Tuple:
            application = Live.Application.get_application()
            return application.get_major_version(), application.get_minor_version()
        self.osc_server.add_handler("/live/application/get_property/version", get_version)
