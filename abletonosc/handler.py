from ableton.v2.control_surface.component import Component
from typing import Optional, Tuple, Any
import logging
from .osc_server import OSCServer

class AbletonOSCHandler(Component):
    def __init__(self, manager):
        super().__init__()

        self.logger = logging.getLogger("abletonosc")
        self.manager = manager
        self.osc_server: OSCServer = self.manager.osc_server
        self.init_api()
        self.listener_functions = {}

    def init_api(self):
        pass

    def clear_api(self):
        pass

    #--------------------------------------------------------------------------------
    # Generic callbacks
    #--------------------------------------------------------------------------------
    def _call_method(self, target, method, params: Optional[Tuple[Any]] = ()):
        self.logger.info("Calling method: %s (params %s)" % (method, str(params)))
        getattr(target, method)(*params)

    def _set_property(self, target, prop, params: Tuple[Any]) -> None:
        self.logger.info("Setting property: %s (new value %s)" % (prop, params[0]))
        setattr(target, prop, params[0])

    def _get_property(self, target, prop, params: Optional[Tuple[Any]] = ()) -> Tuple[Any]:
        self.logger.info("Getting property: %s" % prop)
        return getattr(target, prop),

    def _start_listen(self, target, prop, params: Optional[Tuple[Any]] = ()) -> None:
        def property_changed_callback():
            value = getattr(target, prop)
            self.logger.info("Property %s changed: %s" % (prop, value))
            osc_address = "/live/song/get/%s" % prop
            self.logger.info("Sending to %s" % osc_address)
            self.osc_server.send(osc_address, (value,))

        if prop in self.listener_functions:
            self._stop_listen(target, prop)

        add_listener_function_name = "add_%s_listener" % prop
        add_listener_function = getattr(target, add_listener_function_name)
        add_listener_function(property_changed_callback)
        self.listener_functions[prop] = property_changed_callback

    def _stop_listen(self, target, prop, params: Optional[Tuple[Any]] = ()) -> None:
        if prop in self.listener_functions:
            listener_function = self.listener_functions[prop]
            remove_listener_function_name = "remove_%s_listener" % prop
            remove_listener_function = getattr(target, remove_listener_function_name)
            remove_listener_function(listener_function)
            del self.listener_functions[prop]
        else:
            self.logger.warning("No listener function found for property: %s" % prop)