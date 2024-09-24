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
        "/live/test",
        "/live/application/get/version",
        "/live/api/reload",
        "/live/api/get/log_level",
        "/live/api/set/log_level",
        "/live/startup",
        "/live/error",
        "/live/song/capture_midi",
        "/live/song/continue_playing",
        "/live/song/create_audio_track",
        "/live/song/create_midi_track",
        "/live/song/create_return_track",
        "/live/song/create_scene",
        "/live/song/cue_point/jump",
        "/live/song/delete_scene",
        "/live/song/delete_return_track",
        "/live/song/delete_track",
        "/live/song/duplicate_scene",
        "/live/song/duplicate_track",
        "/live/song/jump_by",
        "/live/song/jump_to_next_cue",
        "/live/song/jump_to_prev_cue",
        "/live/song/redo",
        "/live/song/start_playing",
        "/live/song/stop_playing",
        "/live/song/stop_all_clips",
        "/live/song/tap_tempo",
        "/live/song/trigger_session_record",
        "/live/song/undo",
        "/live/song/get/arrangement_overdub",
        "/live/song/get/back_to_arranger",
        "/live/song/get/can_redo",
        "/live/song/get/can_undo",
        "/live/song/get/clip_trigger_quantization",
        "/live/song/get/current_song_time",
        "/live/song/get/groove_amount",
        "/live/song/get/is_playing",
        "/live/song/get/loop",
        "/live/song/get/loop_length",
        "/live/song/get/loop_start",
        "/live/song/get/metronome",
        "/live/song/get/midi_recording_quantization",
        "/live/song/get/nudge_down",
        "/live/song/get/nudge_up",
        "/live/song/get/punch_in",
        "/live/song/get/punch_out",
        "/live/song/get/record_mode",
        "/live/song/get/session_record",
        "/live/song/get/signature_denominator",
        "/live/song/get/signature_numerator",
        "/live/song/get/song_length",
        "/live/song/get/tempo",
        "/live/song/set/arrangement_overdub",
        "/live/song/set/back_to_arranger",
        "/live/song/set/clip_trigger_quantization",
        "/live/song/set/current_song_time",
        "/live/song/set/groove_amount",
        "/live/song/set/loop",
        "/live/song/set/loop_length",
        "/live/song/set/loop_start",
        "/live/song/set/metronome",
        "/live/song/set/midi_recording_quantization",
        "/live/song/set/nudge_down",
        "/live/song/set/nudge_up",
        "/live/song/set/punch_in",
        "/live/song/set/punch_out",
        "/live/song/set/record_mode",
        "/live/song/set/session_record",
        "/live/song/set/signature_denominator",
        "/live/song/set/signature_numerator",
        "/live/song/set/tempo",
        "/live/song/get/cue_points",
        "/live/song/get/num_scenes",
        "/live/song/get/num_tracks",
        "/live/song/get/track_names",
        "/live/song/get/track_data",
        "/live/song/start_listen/beat",
        "/live/song/stop_listen/beat",
        "/live/song/get/beat",
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
        "/live/track/stop_all_clips",
        "/live/track/get/arm",
        "/live/track/get/available_input_routing_channels",
        "/live/track/get/available_input_routing_types",
        "/live/track/get/available_output_routing_channels",
        "/live/track/get/available_output_routing_types",
        "/live/track/get/can_be_armed",
        "/live/track/get/color",
        "/live/track/get/color_index",
        "/live/track/get/current_monitoring_state",
        "/live/track/get/fired_slot_index",
        "/live/track/get/fold_state",
        "/live/track/get/has_audio_input",
        "/live/track/get/has_audio_output",
        "/live/track/get/has_midi_input",
        "/live/track/get/has_midi_output",
        "/live/track/get/input_routing_channel",
        "/live/track/get/input_routing_type",
        "/live/track/get/output_routing_channel",
        "/live/track/get/output_meter_left",
        "/live/track/get/output_meter_level",
        "/live/track/get/output_meter_right",
        "/live/track/get/output_routing_type",
        "/live/track/get/is_foldable",
        "/live/track/get/is_grouped",
        "/live/track/get/is_visible",
        "/live/track/get/mute",
        "/live/track/get/name",
        "/live/track/get/panning",
        "/live/track/get/playing_slot_index",
        "/live/track/get/send",
        "/live/track/get/solo",
        "/live/track/get/volume",
        "/live/track/set/arm",
        "/live/track/set/color",
        "/live/track/set/color_index",
        "/live/track/set/current_monitoring_state",
        "/live/track/set/fold_state",
        "/live/track/set/input_routing_channel",
        "/live/track/set/input_routing_type",
        "/live/track/set/mute",
        "/live/track/set/name",
        "/live/track/set/output_routing_channel",
        "/live/track/set/output_routing_type",
        "/live/track/set/panning",
        "/live/track/set/send",
        "/live/track/set/solo",
        "/live/track/set/volume",
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
        "/live/clip_slot/create_clip",
        "/live/clip_slot/delete_clip",
        "/live/clip_slot/get/has_clip",
        "/live/clip_slot/get/has_stop_button",
        "/live/clip_slot/set/has_stop_button",
        "/live/clip_slot/duplicate_clip_to",
        "/live/clip/fire",
        "/live/clip/stop",
        "/live/clip/duplicate_loop",
        "/live/clip/get/notes",
        "/live/clip/add/notes",
        "/live/clip/remove/notes",
        "/live/clip/get/color",
        "/live/clip/set/color",
        "/live/clip/get/name",
        "/live/clip/set/name",
        "/live/clip/get/gain",
        "/live/clip/set/gain",
        "/live/clip/get/length",
        "/live/clip/get/pitch_coarse",
        "/live/clip/set/pitch_coarse",
        "/live/clip/get/pitch_fine",
        "/live/clip/set/pitch_fine",
        "/live/clip/get/file_path",
        "/live/clip/get/is_audio_clip",
        "/live/clip/get/is_midi_clip",
        "/live/clip/get/is_playing",
        "/live/clip/get/is_recording",
        "/live/clip/get/playing_position",
        "/live/clip/start_listen/playing_position",
        "/live/clip/stop_listen/playing_position",
        "/live/clip/get/loop_start",
        "/live/clip/set/loop_start",
        "/live/clip/get/loop_end",
        "/live/clip/set/loop_end",
        "/live/clip/get/warping",
        "/live/clip/set/warping",
        "/live/clip/get/start_marker",
        "/live/clip/set/start_marker",
        "/live/clip/get/end_marker",
        "/live/clip/set/end_marker",
        "/live/device/get/name",
        "/live/device/get/class_name",
        "/live/device/get/type",
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
    parser = argparse.ArgumentParser(description="Console client for AbletonOSC with tab completion. Takes OSC commands and parameters, and prints the return value.")
    parser.add_argument("--hostname", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11000)
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode: prints all OSC messages")
    args = parser.parse_args()
    main(args)
