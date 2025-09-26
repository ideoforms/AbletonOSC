from ableton.v2.control_surface import ControlSurface

from . import abletonosc

import importlib
import traceback
import logging
import os

logger = logging.getLogger("abletonosc")

class Manager(ControlSurface):
    def parse_multi_arg_handler(self, params):
        """
        Custom handler for /parse_multi_arg: expects a single string param in the form:
        "[osc command] <arg1> <arg2> <arg3>..."
        Each arg can have a type indicator suffix: (i) for int, (f) for float, (s) for string.
        If no type indicator, will infer type: int if possible, else float, else string.
        Example: "/live/track/volume 0(i) 0.8(f)" or "/live/track/name 1 Hello(s)"
        """
        import re
        if not params or not isinstance(params[0], str):
            logger.warning("parse_multi_arg_handler: Expected a single string param.")
            return ()
        input_str = params[0].strip()
        if not input_str:
            logger.warning("parse_multi_arg_handler: Empty input string.")
            return ()
        # Split into command and args
        parts = input_str.split()
        if not parts:
            logger.warning("parse_multi_arg_handler: No command found in input string.")
            return ()
        target = parts[0]
        arg_strs = parts[1:]
        parsed_args = []
        type_re = re.compile(r"^(.*?)(\((i|f|s|b)\))?$")
        for arg in arg_strs:
            m = type_re.match(arg)
            if not m:
                parsed_args.append(arg)
                continue
            val, _, typ = m.groups()
            val = val.strip()
            if typ == 'i':
                try:
                    parsed_args.append(int(val))
                except Exception:
                    parsed_args.append(val)
            elif typ == 'f':
                try:
                    parsed_args.append(float(val))
                except Exception:
                    parsed_args.append(val)
            elif typ == 's':
                parsed_args.append(val)
            elif typ == 'b':
                # Only treat as boolean if (b) is present
                if val.lower() in ('true', 'yes', 'on'):
                    parsed_args.append(True)
                elif val.lower() in ('false', 'no', 'off'):
                    parsed_args.append(False)
                elif val == '1':
                    parsed_args.append(True)
                elif val == '0':
                    parsed_args.append(False)
                else:
                    parsed_args.append(bool(val))
            else:
                # Infer type: int, then float, then string (do not treat 1/0 as bool)
                try:
                    parsed_args.append(int(val))
                except Exception:
                    try:
                        parsed_args.append(float(val))
                    except Exception:
                        parsed_args.append(val)
        logger.info(f"parse_multi_arg_handler: Forwarding to {target} with args {parsed_args}")
        try:
            self.osc_server.send(target, tuple(parsed_args))
        except Exception as e:
            logger.error(f"parse_multi_arg_handler error: {e}")
        return ()
    def arm_track_solo_handler(self, params):
        """
        Custom handler for /arm_track_solo: disarm tracks 0-7, arm the specified track.
        """
        track_id = int(params[0])
        for i in range(8):
            try:
                if i != track_id:
                    self.song.tracks[i].arm = False
            except Exception:
                pass
        try:
            self.song.tracks[track_id].arm = True
        except Exception:
            pass
        return ()


    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)

        self.log_level = "info"
        self.handlers = []

        # Set up logging to file as early as possible
        module_path = os.path.dirname(os.path.realpath(__file__))
        log_dir = os.path.join(module_path, "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir, 0o755)
        log_path = os.path.join(log_dir, "abletonosc.log")
        self.log_file_handler = logging.FileHandler(log_path)
        self.log_file_handler.setLevel(self.log_level.upper())
        formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
        self.log_file_handler.setFormatter(formatter)
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            logger.addHandler(self.log_file_handler)

        # Load OSC aliases from config.json
        self.osc_aliases = {}
        config_path = os.path.join(module_path, "config.json")
        if os.path.exists(config_path):
            import json
            with open(config_path, "r") as f:
                try:
                    config = json.load(f)
                    self.osc_aliases = config.get("aliases", {})
                    logger.info(f"Loaded config.json successfully from {config_path}")
                    logger.debug(f"Loaded aliases: {list(self.osc_aliases.keys())}")
                except Exception as e:
                    logger.info(f"Failed to load config.json from {config_path}")
                    logger.debug(f"Error details: {e}")
        else:
            logger.info(f"No config.json found at {config_path}")

        try:
            self.osc_server = abletonosc.OSCServer()
            # Patch the OSCServer to support aliasing
            self.osc_server.osc_aliases = {}
            self.osc_server.handle_alias = self.handle_osc_alias

            # Register all aliases from config.json
            for alias_addr, alias_cfg in self.osc_aliases.items():
                alias_type = alias_cfg.get("type", "simple")
                if alias_type == "custom":
                    handler_name = alias_cfg.get("handler")
                    handler_func = getattr(self, handler_name, None)
                    if handler_func:
                        self.osc_server.add_handler(alias_addr, handler_func)
                        logger.info(f"Registered custom handler for {alias_addr}: {handler_name}")
                    else:
                        logger.warning(f"Handler {handler_name} not found for alias {alias_addr}")
                else:
                    # Add to alias mapping for generic alias processing
                    self.osc_server.osc_aliases[alias_addr] = alias_cfg
                    logger.info(f"Registered simple alias for {alias_addr} → {alias_cfg.get('target')}")

            self.schedule_message(0, self.tick)

            self.start_logging()
            self.init_api()

            self.show_message("AbletonOSC: Listening for OSC on port %d" % abletonosc.OSC_LISTEN_PORT)
            logger.info("Started AbletonOSC on address %s" % str(self.osc_server._local_addr))
        except OSError as msg:
            self.show_message("AbletonOSC: Couldn't bind to port %d (%s)" % (abletonosc.OSC_LISTEN_PORT, msg))
            logger.info("Couldn't bind to port %d (%s)" % (abletonosc.OSC_LISTEN_PORT, msg))

    def handle_osc_alias(self, address, params):
        """
        If the address matches an alias, transform the params and return (target_address, new_params), else None.
        Adds detailed debug logging for troubleshooting.
        """
        alias = self.osc_aliases.get(address)
        logger = logging.getLogger("abletonosc.alias")
        if not alias:
            logger.debug(f"[ALIAS] No alias found for address: {address}")
            return None
        target = alias.get("target")
        args_template = alias.get("args", [])
        logger.debug(f"[ALIAS] Matched alias: {address} → {target} | args template: {args_template} | incoming params: {params}")
        new_args = []
        for i, arg in enumerate(args_template):
            if isinstance(arg, str) and arg.startswith("$"):
                try:
                    idx = int(arg[1:]) - 1
                    val = params[idx]
                    logger.debug(f"[ALIAS] Substituting {arg} with param[{idx}] = {val}")
                    new_args.append(val)
                except Exception as e:
                    logger.debug(f"[ALIAS] Failed to substitute {arg}: {e}")
                    new_args.append(None)
            else:
                logger.debug(f"[ALIAS] Using static arg: {arg}")
                new_args.append(arg)
        logger.debug(f"[ALIAS] Final args for {target}: {new_args}")
        return (target, tuple(new_args))


    def start_logging(self):
        """
        Start logging to a local logfile (logs/abletonosc.log),
        and relay error messages via OSC.
        """
        module_path = os.path.dirname(os.path.realpath(__file__))
        log_dir = os.path.join(module_path, "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir, 0o755)
        log_path = os.path.join(log_dir, "abletonosc.log")
        self.log_file_handler = logging.FileHandler(log_path)
        self.log_file_handler.setLevel(self.log_level.upper())
        formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
        self.log_file_handler.setFormatter(formatter)
        logger.addHandler(self.log_file_handler)

        class LiveOSCErrorLogHandler(logging.StreamHandler):
            def emit(handler, record):
                message = record.getMessage()
                message = message[message.index(":") + 2:]
                try:
                    self.osc_server.send("/live/error", (message,))
                except OSError:
                    # If the connection is dead, silently ignore errors as there's not much more we can do
                    pass
        self.live_osc_error_handler = LiveOSCErrorLogHandler()
        self.live_osc_error_handler.setLevel(logging.ERROR)
        logger.addHandler(self.live_osc_error_handler)

    def stop_logging(self):
        logger.removeHandler(self.log_file_handler)
        logger.removeHandler(self.live_osc_error_handler)

    def init_api(self):
        def test_callback(params):
            self.show_message("Received OSC OK")
            self.osc_server.send("/live/test", ("ok",))
        def reload_callback(params):
            self.reload_imports()
        def get_log_level_callback(params):
            return (self.log_level,)
        def set_log_level_callback(params):
            log_level = params[0]
            assert log_level in ("debug", "info", "warning", "error", "critical")
            self.log_level = log_level
            self.log_file_handler.setLevel(self.log_level.upper())

        self.osc_server.add_handler("/live/test", test_callback)
        self.osc_server.add_handler("/live/api/reload", reload_callback)
        self.osc_server.add_handler("/live/api/get/log_level", get_log_level_callback)
        self.osc_server.add_handler("/live/api/set/log_level", set_log_level_callback)

        with self.component_guard():
            self.handlers = [
                abletonosc.SongHandler(self),
                abletonosc.ApplicationHandler(self),
                abletonosc.ClipHandler(self),
                abletonosc.ClipSlotHandler(self),
                abletonosc.TrackHandler(self),
                abletonosc.DeviceHandler(self),
                abletonosc.ViewHandler(self),
                abletonosc.SceneHandler(self)
            ]

    def clear_api(self):
        self.osc_server.clear_handlers()
        for handler in self.handlers:
            handler.clear_api()

    def tick(self):
        """
        Called once per 100ms "tick".
        Live's embedded Python implementation does not appear to support threading,
        and beachballs when a thread is started. Instead, this approach allows long-running
        processes such as the OSC server to perform operations.
        """
        logger.debug("Tick...")
        self.osc_server.process()
        self.schedule_message(1, self.tick)

    def reload_imports(self):
        try:
            importlib.reload(abletonosc.application)
            importlib.reload(abletonosc.clip)
            importlib.reload(abletonosc.clip_slot)
            importlib.reload(abletonosc.device)
            importlib.reload(abletonosc.handler)
            importlib.reload(abletonosc.osc_server)
            importlib.reload(abletonosc.scene)
            importlib.reload(abletonosc.song)
            importlib.reload(abletonosc.track)
            importlib.reload(abletonosc.view)
            importlib.reload(abletonosc)
        except Exception as e:
            exc = traceback.format_exc()
            logging.warning(exc)

        self.clear_api()
        self.init_api()
        logger.info("Reloaded code")

    def disconnect(self):
        self.show_message("Disconnecting...")
        logger.info("Disconnecting...")
        self.stop_logging()
        self.osc_server.shutdown()
        super().disconnect()


