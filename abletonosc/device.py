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
        # Sidechain routing
        #--------------------------------------------------------------------------------
        def device_get_sidechain_available(device, params):
            """List available sidechain routing sources for a device."""
            try:
                # Try to find routing channels for sidechain
                track_index = int(params[0])
                track = self.song.tracks[track_index]
                sources = []
                for i, t in enumerate(self.song.tracks):
                    if i != track_index:
                        sources.append(t.name)
                return tuple(sources)
            except Exception as e:
                self.logger.error("get_sidechain_available failed: %s" % e)
                return ("error", str(e))

        def device_set_sidechain_routing(params):
            """Set a device's sidechain input to a specific track and channel.

            Args:
                params[0]: track_index (int) — track with the compressor
                params[1]: device_index (int) — device index
                params[2]: source (str/int) — track name or index
                params[3]: channel (str, optional) — channel name to match
                           e.g. "Kick" matches "Kick Acoustified 08 1 | Post FX"
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                source = params[2]
                channel_match = str(params[3]).lower() if len(params) > 3 else ""

                track = self.song.tracks[track_index]
                device = track.devices[device_index]

                if not hasattr(device, 'available_input_routing_types'):
                    return ("error", "device does not support sidechain routing")

                available_types = list(device.available_input_routing_types)

                # Find the matching routing type by display_name or index
                target_type = None
                try:
                    idx = int(source)
                    if 0 <= idx < len(available_types):
                        target_type = available_types[idx]
                except (ValueError, TypeError):
                    pass

                if target_type is None:
                    source_str = str(source).lower()
                    for rt in available_types:
                        if hasattr(rt, 'display_name') and source_str in rt.display_name.lower():
                            target_type = rt
                            break

                if target_type is None:
                    names = []
                    for i, rt in enumerate(available_types):
                        name = rt.display_name if hasattr(rt, 'display_name') else str(rt)
                        names.append("%d: %s" % (i, name))
                    return ("error", "source not found. Available: %s" % ", ".join(names))

                device.input_routing_type = target_type
                type_name = target_type.display_name if hasattr(target_type, 'display_name') else str(target_type)
                self.logger.info("Sidechain type set: %s" % type_name)

                # Set channel — match by name or use first
                ch_name = "default"
                if hasattr(device, 'available_input_routing_channels'):
                    channels = list(device.available_input_routing_channels)
                    if channel_match and channels:
                        # Score each channel — best match wins
                        # Priority: name match + "1" (first variation) + "Post FX"
                        best_ch = None
                        best_score = -1
                        best_name = ""
                        for ch in channels:
                            name = ch.display_name if hasattr(ch, 'display_name') else str(ch)
                            name_lower = name.lower()
                            if channel_match not in name_lower:
                                continue
                            score = 0
                            # Prefer "Post FX" (cleanest signal for ducking)
                            if "post fx" in name_lower:
                                score += 10
                            elif "pre fx" in name_lower:
                                score += 5
                            # Prefer variation "1" (first/primary pad)
                            if " 1 " in name or name.endswith(" 1"):
                                score += 3
                            # Penalize "Post Mixer" (level varies with mix)
                            if "post mixer" in name_lower:
                                score -= 2
                            if score > best_score:
                                best_score = score
                                best_ch = ch
                                best_name = name
                        if best_ch:
                            device.input_routing_channel = best_ch
                            ch_name = best_name
                        else:
                            ch_names = [ch.display_name if hasattr(ch, 'display_name') else str(ch)
                                        for ch in channels]
                            self.logger.info("Available channels: %s" % ch_names)
                            return ("error", "channel '%s' not found. Available: %s" %
                                    (channel_match, ", ".join(ch_names)))
                    elif channels:
                        device.input_routing_channel = channels[0]
                        ch_name = channels[0].display_name if hasattr(channels[0], 'display_name') else "first"

                self.logger.info("Sidechain set: track %d device %d -> %s | %s" %
                                 (track_index, device_index, type_name, ch_name))
                return (track_index, device_index, "%s | %s" % (type_name, ch_name))

            except Exception as e:
                self.logger.error("set_sidechain_routing failed: %s" % e)
                return ("error", str(e))

        self.osc_server.add_handler("/live/device/get/sidechain/available",
                                    create_device_callback(device_get_sidechain_available, include_ids=True))
        self.osc_server.add_handler("/live/device/set/sidechain/routing",
                                    device_set_sidechain_routing)

        #--------------------------------------------------------------------------------
        # Instrument Rack chain management
        #--------------------------------------------------------------------------------

        def device_get_num_chains(device, params):
            """Get number of chains in an Instrument/Effect Rack."""
            if not device.can_have_chains:
                return (0,)
            try:
                return (len(device.chains),)
            except Exception:
                return (0,)

        def device_get_chains_info(device, params):
            """Get chain names and device counts for a rack device.

            Returns alternating: name, num_devices, name, num_devices, ...
            """
            if not device.can_have_chains:
                return ("error", "device is not a rack")
            try:
                result = []
                for chain in device.chains:
                    result.append(chain.name)
                    result.append(len(chain.devices))
                return tuple(result)
            except Exception as e:
                return ("error", str(e))

        def device_get_chain_devices(params):
            """Get device names and classes for all devices in a specific chain.

            Params: track_index, device_index, chain_index
            Returns: name, class_name, name, class_name, ...
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                device = self.song.tracks[track_index].devices[device_index]

                if not device.can_have_chains:
                    return ("error", "device is not a rack")

                chains = list(device.chains)
                if chain_index >= len(chains):
                    return ("error", "chain index %d out of range (have %d)" % (chain_index, len(chains)))

                chain = chains[chain_index]
                result = [track_index, device_index, chain_index]
                for dev in chain.devices:
                    result.append(dev.name)
                    result.append(dev.class_name)
                return tuple(result)

            except Exception as e:
                self.logger.error("get_chain_devices failed: %s" % e)
                return ("error", str(e))

        def device_get_chain_parameter_value(params):
            """Get a parameter value from a device inside a chain.

            Params: track_index, device_index, chain_index, chain_device_index, param_index
            Returns: track_index, device_index, chain_index, chain_device_index, param_index, value
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                chain_device_index = int(params[3])
                param_index = int(params[4])

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                chain_device = chain.devices[chain_device_index]
                value = chain_device.parameters[param_index].value

                return (track_index, device_index, chain_index, chain_device_index, param_index, value)

            except Exception as e:
                self.logger.error("get_chain_parameter_value failed: %s" % e)
                return ("error", str(e))

        def device_set_chain_parameter_value(params):
            """Set a parameter value on a device inside a chain.

            Params: track_index, device_index, chain_index, chain_device_index, param_index, value
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                chain_device_index = int(params[3])
                param_index = int(params[4])
                value = float(params[5])

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                chain_device = chain.devices[chain_device_index]
                chain_device.parameters[param_index].value = value

            except Exception as e:
                self.logger.error("set_chain_parameter_value failed: %s" % e)
                return ("error", str(e))

        def device_get_chain_parameters_value(params):
            """Get all parameter values from a device inside a chain.

            Params: track_index, device_index, chain_index, chain_device_index
            Returns: track_index, device_index, chain_index, chain_device_index, val0, val1, ...
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                chain_device_index = int(params[3])

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                chain_device = chain.devices[chain_device_index]

                result = [track_index, device_index, chain_index, chain_device_index]
                for p in chain_device.parameters:
                    result.append(p.value)
                return tuple(result)

            except Exception as e:
                self.logger.error("get_chain_parameters_value failed: %s" % e)
                return ("error", str(e))

        def device_get_chain_parameters_name(params):
            """Get all parameter names from a device inside a chain.

            Params: track_index, device_index, chain_index, chain_device_index
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                chain_device_index = int(params[3])

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                chain_device = chain.devices[chain_device_index]

                result = [track_index, device_index, chain_index, chain_device_index]
                for p in chain_device.parameters:
                    result.append(p.name)
                return tuple(result)

            except Exception as e:
                self.logger.error("get_chain_parameters_name failed: %s" % e)
                return ("error", str(e))

        def device_set_chain_volume(params):
            """Set the mixer volume of a chain (for blending layers).

            Params: track_index, device_index, chain_index, volume (0.0-1.0)
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                volume = float(params[3])

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                chain.mixer_device.volume.value = volume

                return (track_index, device_index, chain_index, volume)

            except Exception as e:
                self.logger.error("set_chain_volume failed: %s" % e)
                return ("error", str(e))

        def device_get_chain_volume(params):
            """Get the mixer volume of a chain.

            Params: track_index, device_index, chain_index
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                volume = chain.mixer_device.volume.value

                return (track_index, device_index, chain_index, volume)

            except Exception as e:
                self.logger.error("get_chain_volume failed: %s" % e)
                return ("error", str(e))

        def device_set_chain_panning(params):
            """Set the panning of a chain.

            Params: track_index, device_index, chain_index, pan (-1.0 to 1.0)
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                pan = float(params[3])

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                chain.mixer_device.panning.value = pan

                return (track_index, device_index, chain_index, pan)

            except Exception as e:
                self.logger.error("set_chain_panning failed: %s" % e)
                return ("error", str(e))

        def device_set_chain_mute(params):
            """Mute/unmute a chain in a rack.

            Params: track_index, device_index, chain_index, mute (0 or 1)
            """
            try:
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                mute = bool(int(params[3]))

                device = self.song.tracks[track_index].devices[device_index]
                chain = device.chains[chain_index]
                chain.mute = mute

                return (track_index, device_index, chain_index, int(mute))

            except Exception as e:
                self.logger.error("set_chain_mute failed: %s" % e)
                return ("error", str(e))

        # Register chain management endpoints
        self.osc_server.add_handler("/live/device/get/num_chains",
                                    create_device_callback(device_get_num_chains))
        self.osc_server.add_handler("/live/device/get/chains/info",
                                    create_device_callback(device_get_chains_info))
        self.osc_server.add_handler("/live/device/get/chain/devices",
                                    device_get_chain_devices)
        self.osc_server.add_handler("/live/device/get/chain/parameter/value",
                                    device_get_chain_parameter_value)
        self.osc_server.add_handler("/live/device/set/chain/parameter/value",
                                    device_set_chain_parameter_value)
        self.osc_server.add_handler("/live/device/get/chain/parameters/value",
                                    device_get_chain_parameters_value)
        self.osc_server.add_handler("/live/device/get/chain/parameters/name",
                                    device_get_chain_parameters_name)
        self.osc_server.add_handler("/live/device/set/chain/volume",
                                    device_set_chain_volume)
        self.osc_server.add_handler("/live/device/get/chain/volume",
                                    device_get_chain_volume)
        self.osc_server.add_handler("/live/device/set/chain/panning",
                                    device_set_chain_panning)
        self.osc_server.add_handler("/live/device/set/chain/mute",
                                    device_set_chain_mute)
