#!/usr/bin/env python3

#--------------------------------------------------------------------------------
# Console client for AbletonOSC with tab completion for API paths.
#
# Takes OSC commands and parameters, and prints the return value.
#--------------------------------------------------------------------------------

import re
import sys
import shlex
import argparse

try:
    import readline
except ImportError:
    if sys.platform == "win32":
        print("On Windows, run-console.py requires pyreadline3: pip install pyreadline3")
    else:
        raise

from client import AbletonOSCClient

class LiveAPICompleter:
    def __init__(self, commands):
        self.commands = sorted(commands)
        self.matches = []

    def complete(self, text, state):
        if state == 0:
            # On first trigger, build possible matches.
            if text:
                self.matches = [s for s in self.commands if s.startswith(text)]
            else:
                self.matches = self.commands[:]
        try:
            return self.matches[state]
        except IndexError:
            return None

def print_error(address, args):
    print("Received error from Live: %s" % args)

def main(args):
    client = AbletonOSCClient(args.hostname, args.port)
    if args.verbose:
        client.verbose = True
    client.set_handler("/live/error", print_error)
    client.send_message("/live/api/reload")

    # List of OSC API paths for tab completion
    words = [
        "/live/application/get/version",
        "/live/application/get/average_process_usage",
        "/live/clip/get/notes",
        "/live/clip/add/notes",
        "/live/clip/remove/notes",
        "/live/clips/filter",
        "/live/clips/unfilter",
        "/live/clip_slot/duplicate_clip_to",
        "/live/device/get/num_parameters",
        "/live/device/get/parameters/name",
        "/live/device/get/parameters/value",
        "/live/device/get/parameters/min",
        "/live/device/get/parameters/max",
        "/live/device/get/parameters/is_quantized",
        "/live/device/set/parameters/value",
        "/live/device/get/parameter/value",
        "/live/device/get/parameter/value_string",
        "/live/device/set/parameter/value",
        "/live/device/get/parameter/name",
        "/live/device/start_listen/parameter/value",
        "/live/device/stop_listen/parameter/value",
        "/live/song/get/num_tracks",
        "/live/song/get/track_names",
        "/live/song/get/track_data",
        "/live/song/export/structure",
        "/live/song/get/num_scenes",
        "/live/song/get/scene_names",
        "/live/song/get/cue_points",
        "/live/song/cue_point/jump",
        "/live/song/start_listen/beat",
        "/live/song/stop_listen/beat",
        "/live/track/get/send",
        "/live/track/set/send",
        "/live/track/delete_clip",
        "/live/track/get/clips/name",
        "/live/track/get/clips/length",
        "/live/track/get/clips/color",
        "/live/track/get/arrangement_clips/name",
        "/live/track/get/arrangement_clips/length",
        "/live/track/get/arrangement_clips/start_time",
        "/live/track/get/num_devices",
        "/live/track/get/devices/name",
        "/live/track/get/devices/type",
        "/live/track/get/devices/class_name",
        "/live/track/get/devices/can_have_chains",
        "/live/track/get/available_output_routing_types",
        "/live/track/get/available_output_routing_channels",
        "/live/track/get/output_routing_type",
        "/live/track/set/output_routing_type",
        "/live/track/get/output_routing_channel",
        "/live/track/set/output_routing_channel",
        "/live/track/get/available_input_routing_types",
        "/live/track/get/available_input_routing_channels",
        "/live/track/get/input_routing_type",
        "/live/track/set/input_routing_type",
        "/live/track/get/input_routing_channel",
        "/live/track/set/input_routing_channel",
        "/live/view/get/selected_scene",
        "/live/view/get/selected_track",
        "/live/view/get/selected_clip",
        "/live/view/get/selected_device",
        "/live/view/set/selected_scene",
        "/live/view/set/selected_track",
        "/live/view/set/selected_clip",
        "/live/view/set/selected_device",
        "/live/view/start_listen/selected_scene",
        "/live/view/start_listen/selected_track",
        "/live/view/stop_listen/selected_scene",
        "/live/view/stop_listen/selected_track",
        "/live/test",
        "/live/api/reload",
        "/live/api/get/log_level",
        "/live/api/set/log_level",
        # Add more addresses as needed
    ]

    completer = LiveAPICompleter(words)
    readline.set_completer(completer.complete)

    # Adjust the completer delimiters to not consider '/' as a word boundary
    readline.set_completer_delims(readline.get_completer_delims().replace('/', ''))

    # Detect if we're using libedit (macOS default) or GNU readline
    if 'libedit' in readline.__doc__:
        # macOS libedit syntax
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        # GNU readline syntax
        readline.parse_and_bind("tab: complete")

    print("AbletonOSC command console with tab completion")
    print("Usage: /live/osc/command [params]")
    print("Type 'quit' or 'exit' to exit the console.")

    while True:
        try:
            command_str = input(">>> ")
        except EOFError:
            print()
            break

        # Check if the user wants to exit
        if command_str.strip().lower() in ('quit', 'exit'):
            print("Exiting console.")
            break

        if not re.search("\\w", command_str):
            # Command is empty
            continue
        if not re.search("^/", command_str):
            # Command is invalid
            print("OSC address must begin with a slash (/)")
            continue

        # Parse command-line, with support for quoted strings
        command, *params_str = shlex.split(command_str)
        params = []
        for part in params_str:
            try:
                part = int(part)
            except ValueError:
                try:
                    part = float(part)
                except ValueError:
                    pass
            params.append(part)
        try:
            rv = client.query(command, params)
            rv = ", ".join(str(part) for part in rv)
            print(rv)
        except RuntimeError:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Console client for AbletonOSC. Takes OSC commands and parameters, and prints the return value.")
    parser.add_argument("--hostname", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11000)
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode: prints all OSC messages")
    args = parser.parse_args()
    main(args)
