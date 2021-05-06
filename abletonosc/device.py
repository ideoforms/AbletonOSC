from typing import Tuple, Any
from .component import AbletonOSCComponent

class DeviceComponent(AbletonOSCComponent):
    def init_api(self):
        def create_device_callback(func, *args):
            def device_callback(params: Tuple[Any]):
                track_index, device_index = params[:2]
                device = self.song.tracks[track_index].devices[device_index]
                return func(device, *args, params[2:])

            return device_callback

        methods = [
        ]
        properties_r = [
            "class_name",
            "name",
            "type"
        ]
        properties_rw = [
        ]

        for method in methods:
            self.osc_server.add_handler("/live/device/%s" % method,
                                        create_device_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/device/get_property/%s" % prop,
                                        create_device_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/device/start_property_listen/%s" % prop,
                                        create_device_callback(self._start_property_listen, prop))
            self.osc_server.add_handler("/live/device/stop_property_listen/%s" % prop,
                                        create_device_callback(self._stop_property_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/device/set_property/%s" % prop,
                                        create_device_callback(self._set_property, prop))