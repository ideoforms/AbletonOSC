from typing import Tuple, Any
from .handler import AbletonOSCHandler

class ChainHandler(AbletonOSCHandler):
    """
    Handler for OSC messages related to rack chains and their devices.
    Provides access to chains within rack devices and the devices within those chains.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "chain"

    def init_api(self):
        #--------------------------------------------------------------------------------
        # Callback factory: Rack, Chain, Device operations
        #--------------------------------------------------------------------------------
        def create_rack_callback(func, *args):
            def rack_callback(params: Tuple[Any]):
                track_index, rack_device_index = int(params[0]), int(params[1])
                rack_device = self.song.tracks[track_index].devices[rack_device_index]
                rv = func(rack_device, *args, params[2:])

                if rv is not None:
                    return (track_index, rack_device_index, *rv)

            return rack_callback

        def create_chain_callback(func, *args):
            def chain_callback(params: Tuple[Any]):
                track_index, rack_device_index, chain_index = int(params[0]), int(params[1]), int(params[2])
                chain = self.song.tracks[track_index].devices[rack_device_index].chains[chain_index]
                rv = func(chain, *args, params[3:])

                if rv is not None:
                    return (track_index, rack_device_index, chain_index, *rv)

            return chain_callback

        chain_methods = [
        ]
        chain_properties_r = [
            "has_audio_input",
            "has_audio_output",
            "has_midi_input",
            "has_midi_output",
            "is_auto_colored",
            "muted_via_solo",
            "color_index"
        ]
        chain_properties_rw = [
            "name",
            "color",
            "mute",
            "solo"
        ]

        for method in chain_methods:
            self.osc_server.add_handler("/live/chain/%s" % method, create_chain_callback(self._call_method, method))

        for prop in chain_properties_r + chain_properties_rw:
            self.osc_server.add_handler("/live/chain/get/%s" % prop, create_chain_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/chain/start_listen/%s" % prop, create_chain_callback(self._start_listen, prop))
            self.osc_server.add_handler("/live/chain/stop_listen/%s" % prop, create_chain_callback(self._stop_listen, prop))
        for prop in chain_properties_rw:
            self.osc_server.add_handler("/live/chain/set/%s" % prop,
                                        create_chain_callback(self._set_property, prop))

        def create_chain_device_callback(func, *args):
            def chain_device_callback(params: Tuple[Any]):
                track_index, rack_device_index, chain_index, chain_device_index = int(params[0]), int(params[1]), int(params[2]), int(params[3])
                chain = self.song.tracks[track_index].devices[rack_device_index].chains[chain_index]
                device = chain.devices[chain_device_index]
                rv = func(device, *args, params[4:])

                if rv is not None:
                    return (track_index, rack_device_index, chain_index, chain_device_index, *rv)

            return chain_device_callback

        chain_device_methods = [
        ]
        chain_device_properties_r = [
            "class_name",
            "name",
            "type"
        ]
        chain_device_properties_rw = [
        ]

        for method in chain_device_methods:
            self.osc_server.add_handler("/live/chain/device/%s" % method, create_chain_device_callback(self._call_method, method))

        for prop in chain_device_properties_r + chain_device_properties_rw:
            self.osc_server.add_handler("/live/chain/device/get/%s" % prop, create_chain_device_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/chain/device/start_listen/%s" % prop, create_chain_device_callback(self._start_listen, prop))
            self.osc_server.add_handler("/live/chain/device/stop_listen/%s" % prop, create_chain_device_callback(self._stop_listen, prop))
        for prop in chain_device_properties_rw:
            self.osc_server.add_handler("/live/chain/device/set/%s" % prop, create_chain_device_callback(self._set_property, prop))


        #--------------------------------------------------------------------------------
        # Chain-specific functions
        #--------------------------------------------------------------------------------
        def rack_device_get_num_chains(rack_device, params: Tuple[Any] = ()):
            return len(rack_device.chains),

        def chain_get_num_devices(chain, params: Tuple[Any] = ()):
            return len(chain.devices),

        def chain_get_device_names(chain, params: Tuple[Any] = ()):
            return tuple(device.name for device in chain.devices)

        def chain_get_device_types(chain, params: Tuple[Any] = ()):
            return tuple(device.type for device in chain.devices)

        self.osc_server.add_handler("/live/device/get/num_chains", create_rack_callback(rack_device_get_num_chains))
        self.osc_server.add_handler("/live/chain/get/num_devices", create_chain_callback(chain_get_num_devices))
        self.osc_server.add_handler("/live/chain/device/get/devices/name", create_chain_callback(chain_get_device_names))
        self.osc_server.add_handler("/live/chain/device/get/devices/type", create_chain_callback(chain_get_device_types))

        #--------------------------------------------------------------------------------
        # Chain device: Get/set parameter lists
        #--------------------------------------------------------------------------------
        def chain_device_get_num_parameters(device, params: Tuple[Any] = ()):
            return len(device.parameters),

        def chain_device_get_parameters_name(device, params: Tuple[Any] = ()):
            return tuple(parameter.name for parameter in device.parameters)

        def chain_device_get_parameters_value(device, params: Tuple[Any] = ()):
            return tuple(parameter.value for parameter in device.parameters)

        def chain_device_get_parameters_min(device, params: Tuple[Any] = ()):
            return tuple(parameter.min for parameter in device.parameters)

        def chain_device_get_parameters_max(device, params: Tuple[Any] = ()):
            return tuple(parameter.max for parameter in device.parameters)

        def chain_device_get_parameters_is_quantized(device, params: Tuple[Any] = ()):
            return tuple(parameter.is_quantized for parameter in device.parameters)

        def chain_device_set_parameters_value(device, params: Tuple[Any] = ()):
            for index, value in enumerate(params):
                device.parameters[index].value = value

        self.osc_server.add_handler("/live/chain/device/get/num_parameters", create_chain_device_callback(chain_device_get_num_parameters))
        self.osc_server.add_handler("/live/chain/device/get/parameters/name", create_chain_device_callback(chain_device_get_parameters_name))
        self.osc_server.add_handler("/live/chain/device/get/parameters/value", create_chain_device_callback(chain_device_get_parameters_value))
        self.osc_server.add_handler("/live/chain/device/get/parameters/min", create_chain_device_callback(chain_device_get_parameters_min))
        self.osc_server.add_handler("/live/chain/device/get/parameters/max", create_chain_device_callback(chain_device_get_parameters_max))
        self.osc_server.add_handler("/live/chain/device/get/parameters/is_quantized", create_chain_device_callback(chain_device_get_parameters_is_quantized))
        self.osc_server.add_handler("/live/chain/device/set/parameters/value", create_chain_device_callback(chain_device_set_parameters_value))

        #--------------------------------------------------------------------------------
        # Chain device: Get/set individual parameters
        #--------------------------------------------------------------------------------
        def chain_device_get_parameter_value(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return param_index, device.parameters[param_index].value

        def chain_device_get_parameter_value_string(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return param_index, device.parameters[param_index].str_for_value(device.parameters[param_index].value)

        def chain_device_set_parameter_value(device, params: Tuple[Any] = ()):
            param_index, param_value = params[:2]
            param_index = int(param_index)
            device.parameters[param_index].value = param_value

        def chain_device_get_parameter_name(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return param_index, device.parameters[param_index].name

        self.osc_server.add_handler("/live/chain/device/get/parameter/value", create_chain_device_callback(chain_device_get_parameter_value))
        self.osc_server.add_handler("/live/chain/device/get/parameter/value_string", create_chain_device_callback(chain_device_get_parameter_value_string))
        self.osc_server.add_handler("/live/chain/device/get/parameter/name", create_chain_device_callback(chain_device_get_parameter_name))
        self.osc_server.add_handler("/live/chain/device/set/parameter/value", create_chain_device_callback(chain_device_set_parameter_value))