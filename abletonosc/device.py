from typing import Tuple, Any
from .handler import AbletonOSCHandler

class DeviceHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "device"

    def init_api(self):
        def create_device_callback(func, *args, include_ids: bool = False):
            def device_callback(params: Tuple[Any]):
                track_index, device_index = int(params[0]), int(params[1])
                device = self.song.tracks[track_index].devices[device_index]
                if (include_ids):
                    rv = func(device, *args, params[0:])
                else:
                    rv = func(device, *args, params[2:])

                if rv is not None:
                    return (track_index, device_index, *rv)

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
            self.osc_server.add_handler("/live/device/get/%s" % prop,
                                        create_device_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/device/start_listen/%s" % prop,
                                        create_device_callback(self._start_listen, prop))
            self.osc_server.add_handler("/live/device/stop_listen/%s" % prop,
                                        create_device_callback(self._stop_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/device/set/%s" % prop,
                                        create_device_callback(self._set_property, prop))

        #--------------------------------------------------------------------------------
        # Device: Get/set parameter lists
        #--------------------------------------------------------------------------------
        def device_get_num_parameters(device, params: Tuple[Any] = ()):
            return len(device.parameters),

        def device_get_parameters_name(device, params: Tuple[Any] = ()):
            return tuple(parameter.name for parameter in device.parameters)

        def device_get_parameters_value(device, params: Tuple[Any] = ()):
            return tuple(parameter.value for parameter in device.parameters)

        def device_get_parameters_min(device, params: Tuple[Any] = ()):
            return tuple(parameter.min for parameter in device.parameters)

        def device_get_parameters_max(device, params: Tuple[Any] = ()):
            return tuple(parameter.max for parameter in device.parameters)

        def device_get_parameters_is_quantized(device, params: Tuple[Any] = ()):
            return tuple(parameter.is_quantized for parameter in device.parameters)

        def device_set_parameters_value(device, params: Tuple[Any] = ()):
            for index, value in enumerate(params):
                device.parameters[index].value = value

        self.osc_server.add_handler("/live/device/get/num_parameters", create_device_callback(device_get_num_parameters))
        self.osc_server.add_handler("/live/device/get/parameters/name", create_device_callback(device_get_parameters_name))
        self.osc_server.add_handler("/live/device/get/parameters/value", create_device_callback(device_get_parameters_value))
        self.osc_server.add_handler("/live/device/get/parameters/min", create_device_callback(device_get_parameters_min))
        self.osc_server.add_handler("/live/device/get/parameters/max", create_device_callback(device_get_parameters_max))
        self.osc_server.add_handler("/live/device/get/parameters/is_quantized", create_device_callback(device_get_parameters_is_quantized))
        self.osc_server.add_handler("/live/device/set/parameters/value", create_device_callback(device_set_parameters_value))

        #--------------------------------------------------------------------------------
        # Device: Get/set individual parameters
        #--------------------------------------------------------------------------------
        def device_get_parameter_value(device, params: Tuple[Any] = ()):
            # Cast to ints so that we can tolerate floats from interfaces such as TouchOSC
            # that send floats by default.
            # https://github.com/ideoforms/AbletonOSC/issues/33
            param_index = int(params[0])
            return param_index, device.parameters[param_index].value
        
        # Uses str_for_value method to return the UI-friendly version of a parameter value (ex: "2500 Hz")
        def device_get_parameter_value_string(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return param_index, device.parameters[param_index].str_for_value(device.parameters[param_index].value)
        
        def device_get_parameter_value_listener(device, params: Tuple[Any] = ()):

            def property_changed_callback():
                value = device.parameters[params[2]].value
                self.logger.info("Property %s changed of %s %s: %s" % ('value', 'device parameter', str(params), value))
                self.osc_server.send("/live/device/get/parameter/value", (*params, value,))

                value_string = device.parameters[params[2]].str_for_value(device.parameters[params[2]].value)
                self.logger.info("Property %s changed of %s %s: %s" % ('value_string', 'device parameter', str(params), value_string))
                self.osc_server.send("/live/device/get/parameter/value_string", (*params, value_string,))

            listener_key = ('device_parameter_value', tuple(params))
            if listener_key in self.listener_functions:
               device_get_parameter_remove_value_listener(device, params)

            self.logger.info("Adding listener for %s %s, property: %s" % ('device parameter', str(params), 'value'))
            device.parameters[params[2]].add_value_listener(property_changed_callback)
            self.listener_functions[listener_key] = property_changed_callback

            property_changed_callback()

        def device_get_parameter_remove_value_listener(device, params: Tuple[Any] = ()):
            listener_key = ('device_parameter_value', tuple(params))
            if listener_key in self.listener_functions:
                self.logger.info("Removing listener for %s %s, property %s" % (self.class_identifier, str(params), 'value'))
                listener_function = self.listener_functions[listener_key]
                device.parameters[params[2]].remove_value_listener(listener_function)
                del self.listener_functions[listener_key]
            else:
                self.logger.warning("No listener function found for property: %s (%s)" % (prop, str(params)))

        def device_set_parameter_value(device, params: Tuple[Any] = ()):
            param_index, param_value = params[:2]
            param_index = int(param_index)
            device.parameters[param_index].value = param_value

        def device_get_parameter_name(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return param_index, device.parameters[param_index].name

        self.osc_server.add_handler("/live/device/get/parameter/value", create_device_callback(device_get_parameter_value))
        self.osc_server.add_handler("/live/device/get/parameter/value_string", create_device_callback(device_get_parameter_value_string))
        self.osc_server.add_handler("/live/device/set/parameter/value", create_device_callback(device_set_parameter_value))
        self.osc_server.add_handler("/live/device/get/parameter/name", create_device_callback(device_get_parameter_name))
        self.osc_server.add_handler("/live/device/start_listen/parameter/value", create_device_callback(device_get_parameter_value_listener, include_ids = True))
        self.osc_server.add_handler("/live/device/stop_listen/parameter/value", create_device_callback(device_get_parameter_remove_value_listener, include_ids = True))

        #--------------------------------------------------------------------------------
        # PluginDevice: Get all plugin parameters via bank system
        # Returns all parameters across all banks, not just configured ones
        #--------------------------------------------------------------------------------
        def device_get_plugin_all_params(device, params: Tuple[Any] = ()):
            """Get all parameter names from a plugin device using get_parameter_names."""
            result = []
            try:
                # get_parameter_names returns the full list of AU/VST parameter names
                names = device.get_parameter_names(512)  # request up to 512 names
                result.append(len(names))
                for name in names:
                    result.append(name)
            except Exception as e:
                result.append("error:" + str(e))
                # Fallback: try with different count
                try:
                    names = device.get_parameter_names()
                    result.append(len(names))
                    for name in names:
                        result.append(name)
                except Exception as e2:
                    result.append("error2:" + str(e2))
            return tuple(result)

        def device_get_presets(device, params: Tuple[Any] = ()):
            """Get preset list from a plugin device."""
            result = []
            try:
                presets = list(device.presets)
                result.append(len(presets))
                for p in presets:
                    result.append(str(p))
            except Exception as e:
                result.append("error:" + str(e))
            return tuple(result)

        self.osc_server.add_handler("/live/device/get/plugin_all_params", create_device_callback(device_get_plugin_all_params))
        self.osc_server.add_handler("/live/device/get/presets", create_device_callback(device_get_presets))

        #--------------------------------------------------------------------------------
        # Flat device addressing — walks into racks/chains so nested devices
        # can be accessed by a single flat index per track.
        #--------------------------------------------------------------------------------
        def _flatten_devices(device_list):
            """Recursively collect all devices, walking into racks/chains."""
            result = []
            for device in device_list:
                result.append(device)
                if device.can_have_chains:
                    for chain in device.chains:
                        result.extend(_flatten_devices(chain.devices))
            return result

        def flat_device_callback(func):
            def callback(params: Tuple[Any]):
                track_index = int(params[0])
                flat_index = int(params[1])
                all_devices = _flatten_devices(self.song.tracks[track_index].devices)
                device = all_devices[flat_index]
                rv = func(device, params[2:])
                if rv is not None:
                    return (track_index, flat_index, *rv)
            return callback

        def flat_get_name(device, params):
            return device.name,

        def flat_get_class_name(device, params):
            return device.class_name,

        def flat_get_parameters_name(device, params):
            return tuple(p.name for p in device.parameters)

        def flat_get_parameters_value(device, params):
            return tuple(p.value for p in device.parameters)

        def flat_get_parameters_min(device, params):
            return tuple(p.min for p in device.parameters)

        def flat_get_parameters_max(device, params):
            return tuple(p.max for p in device.parameters)

        def flat_set_parameter_value(device, params):
            param_index = int(params[0])
            param_value = float(params[1])
            device.parameters[param_index].value = param_value

        def flat_refresh_parameters(device, params):
            """Re-set all parameter values wrapped in begin/end gesture to force plugin GUI update."""
            count = 0
            for param in device.parameters:
                try:
                    val = param.value
                    param.begin_gesture()
                    param.value = val
                    param.end_gesture()
                    count += 1
                except Exception:
                    pass
            return (count,)

        #--------------------------------------------------------------------------------
        # CompressorDevice: sidechain routing
        # Only CompressorDevice has a specialized LOM class with routing properties.
        # class_name == "Compressor2" in the LOM.
        #--------------------------------------------------------------------------------
        def compressor_get_available_input_routing_types(device, params):
            return tuple(rt.display_name for rt in device.available_input_routing_types)

        def compressor_get_available_input_routing_channels(device, params):
            return tuple(ch.display_name for ch in device.available_input_routing_channels)

        def compressor_get_input_routing_type(device, params):
            return device.input_routing_type.display_name,

        def compressor_set_input_routing_type(device, params):
            type_name = str(params[0])
            for rt in device.available_input_routing_types:
                if rt.display_name == type_name:
                    device.input_routing_type = rt
                    return
            self.logger.warning("Compressor: couldn't find input routing type: %s" % type_name)

        def compressor_get_input_routing_channel(device, params):
            return device.input_routing_channel.display_name,

        def compressor_set_input_routing_channel(device, params):
            channel_name = str(params[0])
            for ch in device.available_input_routing_channels:
                if ch.display_name == channel_name:
                    device.input_routing_channel = ch
                    return
            self.logger.warning("Compressor: couldn't find input routing channel: %s" % channel_name)

        self.osc_server.add_handler("/live/device/get/compressor/available_input_routing_types",
                                    create_device_callback(compressor_get_available_input_routing_types))
        self.osc_server.add_handler("/live/device/get/compressor/available_input_routing_channels",
                                    create_device_callback(compressor_get_available_input_routing_channels))
        self.osc_server.add_handler("/live/device/get/compressor/input_routing_type",
                                    create_device_callback(compressor_get_input_routing_type))
        self.osc_server.add_handler("/live/device/set/compressor/input_routing_type",
                                    create_device_callback(compressor_set_input_routing_type))
        self.osc_server.add_handler("/live/device/get/compressor/input_routing_channel",
                                    create_device_callback(compressor_get_input_routing_channel))
        self.osc_server.add_handler("/live/device/set/compressor/input_routing_channel",
                                    create_device_callback(compressor_set_input_routing_channel))

        def _require_compressor(func):
            def wrapper(device, params):
                if device.class_name != "Compressor2":
                    self.logger.warning("flat_device compressor endpoint called on %s (not Compressor2)" % device.class_name)
                    return
                return func(device, params)
            return wrapper

        self.osc_server.add_handler("/live/flat_device/get/compressor/available_input_routing_types",
                                    flat_device_callback(_require_compressor(compressor_get_available_input_routing_types)))
        self.osc_server.add_handler("/live/flat_device/get/compressor/available_input_routing_channels",
                                    flat_device_callback(_require_compressor(compressor_get_available_input_routing_channels)))
        self.osc_server.add_handler("/live/flat_device/get/compressor/input_routing_type",
                                    flat_device_callback(_require_compressor(compressor_get_input_routing_type)))
        self.osc_server.add_handler("/live/flat_device/set/compressor/input_routing_type",
                                    flat_device_callback(_require_compressor(compressor_set_input_routing_type)))
        self.osc_server.add_handler("/live/flat_device/get/compressor/input_routing_channel",
                                    flat_device_callback(_require_compressor(compressor_get_input_routing_channel)))
        self.osc_server.add_handler("/live/flat_device/set/compressor/input_routing_channel",
                                    flat_device_callback(_require_compressor(compressor_set_input_routing_channel)))

        self.osc_server.add_handler("/live/flat_device/refresh_parameters", flat_device_callback(flat_refresh_parameters))
        self.osc_server.add_handler("/live/flat_device/get/name", flat_device_callback(flat_get_name))
        self.osc_server.add_handler("/live/flat_device/get/class_name", flat_device_callback(flat_get_class_name))
        self.osc_server.add_handler("/live/flat_device/get/parameters/name", flat_device_callback(flat_get_parameters_name))
        self.osc_server.add_handler("/live/flat_device/get/parameters/value", flat_device_callback(flat_get_parameters_value))
        self.osc_server.add_handler("/live/flat_device/get/parameters/min", flat_device_callback(flat_get_parameters_min))
        self.osc_server.add_handler("/live/flat_device/get/parameters/max", flat_device_callback(flat_get_parameters_max))
        self.osc_server.add_handler("/live/flat_device/set/parameter/value", flat_device_callback(flat_set_parameter_value))
