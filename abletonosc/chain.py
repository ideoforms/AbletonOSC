from typing import Tuple, Any
from .handler import AbletonOSCHandler
import logging

logger = logging.getLogger("abletonosc")


class ChainHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "chain"

    def _resolve_rack(self, params):
        """Resolve (track_param, device_index) to a rack device.
        Returns (device, track_id, device_index).
        Raises ValueError if device is not a rack.
        """
        track, track_id = self._resolve_track(params[0])
        device_index = int(params[1])
        device = track.devices[device_index]
        if not self._has_chains(device):
            raise ValueError("Device %d on track %s is not a rack" % (device_index, track_id))
        return device, track_id, device_index

    def init_api(self):

        # ---- Callback factories ----

        def create_chain_callback(func, *args):
            """Resolves (track, rack_device, chain_index, ...) → chain object."""
            def chain_callback(params: Tuple[Any]):
                device, track_id, device_index = self._resolve_rack(params)
                chain_index = int(params[2])
                chain = device.chains[chain_index]
                rv = func(chain, *args, params[3:])
                if rv is not None:
                    return (track_id, device_index, chain_index, *rv)
            return chain_callback

        def create_chain_device_callback(func, *args):
            """Resolves (track, rack, chain, device, ...) → chain device."""
            def chain_device_callback(params: Tuple[Any]):
                device, track_id, rack_device_index = self._resolve_rack(params)
                chain_index = int(params[2])
                chain = device.chains[chain_index]
                chain_device_index = int(params[3])
                chain_device = chain.devices[chain_device_index]
                rv = func(chain_device, *args, params[4:])
                if rv is not None:
                    return (track_id, rack_device_index, chain_index, chain_device_index, *rv)
            return chain_device_callback

        # ---- Chain properties ----

        chain_properties_r = [
            "has_audio_input",
            "has_audio_output",
            "has_midi_input",
            "has_midi_output",
            "is_auto_colored",
            "muted_via_solo",
        ]
        chain_properties_rw = [
            "color",
            "color_index",
            "mute",
            "name",
            "solo",
        ]

        for prop in chain_properties_r + chain_properties_rw:
            self.osc_server.add_handler("/live/chain/get/%s" % prop,
                                        create_chain_callback(self._get_property, prop))
        for prop in chain_properties_rw:
            self.osc_server.add_handler("/live/chain/set/%s" % prop,
                                        create_chain_callback(self._set_property, prop))

        # ---- Chain mixer (volume/panning via chain.mixer_device) ----

        def chain_get_volume(chain, params: Tuple[Any] = ()):
            return (chain.mixer_device.volume.value,)

        def chain_set_volume(chain, params: Tuple[Any] = ()):
            chain.mixer_device.volume.value = float(params[0])

        def chain_get_panning(chain, params: Tuple[Any] = ()):
            return (chain.mixer_device.panning.value,)

        def chain_set_panning(chain, params: Tuple[Any] = ()):
            chain.mixer_device.panning.value = float(params[0])

        self.osc_server.add_handler("/live/chain/get/volume", create_chain_callback(chain_get_volume))
        self.osc_server.add_handler("/live/chain/set/volume", create_chain_callback(chain_set_volume))
        self.osc_server.add_handler("/live/chain/get/panning", create_chain_callback(chain_get_panning))
        self.osc_server.add_handler("/live/chain/set/panning", create_chain_callback(chain_set_panning))

        # ---- Chain device discovery ----

        def chain_get_num_devices(chain, params: Tuple[Any] = ()):
            return (len(chain.devices),)

        def chain_get_device_names(chain, params: Tuple[Any] = ()):
            return tuple(d.name for d in chain.devices)

        def chain_get_device_types(chain, params: Tuple[Any] = ()):
            return tuple(d.type for d in chain.devices)

        def chain_get_device_class_names(chain, params: Tuple[Any] = ()):
            return tuple(d.class_name for d in chain.devices)

        def chain_get_device_can_have_chains(chain, params: Tuple[Any] = ()):
            return tuple(d.can_have_chains for d in chain.devices)

        self.osc_server.add_handler("/live/chain/get/num_devices", create_chain_callback(chain_get_num_devices))
        self.osc_server.add_handler("/live/chain/device/get/devices/name", create_chain_callback(chain_get_device_names))
        self.osc_server.add_handler("/live/chain/device/get/devices/type", create_chain_callback(chain_get_device_types))
        self.osc_server.add_handler("/live/chain/device/get/devices/class_name", create_chain_callback(chain_get_device_class_names))
        self.osc_server.add_handler("/live/chain/device/get/devices/can_have_chains", create_chain_callback(chain_get_device_can_have_chains))

        # ---- Chain device parameters (bulk) ----

        def chain_device_get_num_parameters(device, params: Tuple[Any] = ()):
            return (len(device.parameters),)

        def chain_device_get_parameters_name(device, params: Tuple[Any] = ()):
            return tuple(p.name for p in device.parameters)

        def chain_device_get_parameters_value(device, params: Tuple[Any] = ()):
            return tuple(p.value for p in device.parameters)

        def chain_device_get_parameters_min(device, params: Tuple[Any] = ()):
            return tuple(p.min for p in device.parameters)

        def chain_device_get_parameters_max(device, params: Tuple[Any] = ()):
            return tuple(p.max for p in device.parameters)

        def chain_device_get_parameters_is_quantized(device, params: Tuple[Any] = ()):
            return tuple(p.is_quantized for p in device.parameters)

        self.osc_server.add_handler("/live/chain/device/get/num_parameters", create_chain_device_callback(chain_device_get_num_parameters))
        self.osc_server.add_handler("/live/chain/device/get/parameters/name", create_chain_device_callback(chain_device_get_parameters_name))
        self.osc_server.add_handler("/live/chain/device/get/parameters/value", create_chain_device_callback(chain_device_get_parameters_value))
        self.osc_server.add_handler("/live/chain/device/get/parameters/min", create_chain_device_callback(chain_device_get_parameters_min))
        self.osc_server.add_handler("/live/chain/device/get/parameters/max", create_chain_device_callback(chain_device_get_parameters_max))
        self.osc_server.add_handler("/live/chain/device/get/parameters/is_quantized", create_chain_device_callback(chain_device_get_parameters_is_quantized))

        # ---- Chain device parameters (individual) ----

        def chain_device_get_parameter_value(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return (param_index, device.parameters[param_index].value)

        def chain_device_get_parameter_name(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return (param_index, device.parameters[param_index].name)

        def chain_device_get_parameter_value_string(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return (param_index, device.parameters[param_index].str_for_value(device.parameters[param_index].value))

        def chain_device_set_parameter_value(device, params: Tuple[Any] = ()):
            param_index, param_value = int(params[0]), params[1]
            device.parameters[param_index].value = param_value

        self.osc_server.add_handler("/live/chain/device/get/parameter/value", create_chain_device_callback(chain_device_get_parameter_value))
        self.osc_server.add_handler("/live/chain/device/get/parameter/name", create_chain_device_callback(chain_device_get_parameter_name))
        self.osc_server.add_handler("/live/chain/device/get/parameter/value_string", create_chain_device_callback(chain_device_get_parameter_value_string))
        self.osc_server.add_handler("/live/chain/device/set/parameter/value", create_chain_device_callback(chain_device_set_parameter_value))

        # ---- Sidechain routing ----

        def sidechain_get_available(params: Tuple[Any]):
            """List available sidechain input sources for a device.
            /live/chain/get/sidechain/available (track, device_index)
            """
            track, track_id = self._resolve_track(params[0])
            device_index = int(params[1])
            device = track.devices[device_index]
            result = []
            try:
                for p in device.parameters:
                    if "sidechain" in p.name.lower() or "side-chain" in p.name.lower():
                        if p.is_quantized:
                            result.append(p.name)
                            result.append(p.str_for_value(p.value))
                            result.append(p.min)
                            result.append(p.max)
            except Exception as e:
                logger.warning("Error reading sidechain params: %s" % e)
            return tuple(result) if result else ("no_sidechain",)

        def sidechain_set_routing(params: Tuple[Any]):
            """Set sidechain routing for a device.
            /live/chain/set/sidechain/routing (track, device_index, param_name, value)
            """
            track, track_id = self._resolve_track(params[0])
            device_index = int(params[1])
            device = track.devices[device_index]
            param_name = str(params[2])
            value = params[3]
            for p in device.parameters:
                if p.name.lower() == param_name.lower():
                    p.value = float(value)
                    logger.info("Set sidechain %s = %s on device %d" % (param_name, value, device_index))
                    return (track_id, device_index, param_name, p.value)
            raise ValueError("Sidechain parameter not found: %s" % param_name)

        self.osc_server.add_handler("/live/chain/get/sidechain/available", sidechain_get_available)
        self.osc_server.add_handler("/live/chain/set/sidechain/routing", sidechain_set_routing)