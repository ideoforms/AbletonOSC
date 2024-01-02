#!/usr/bin/env python3

#--------------------------------------------------------------------------------
# Console client for AbletonOSC.
#
# Takes OSC commands and parameters, and prints the return value.
#--------------------------------------------------------------------------------

import re
import sys
import shlex
import argparse

try:
    import readline
except:
    if sys.platform == "win32":
        print("On Windows, run-console.py requires pyreadline3: pip install pyreadline3")
    else:
        raise

from client import AbletonOSCClient

class LiveAPICompleter:
    def __init__(self, commands):
        self.commands = commands

    def complete(self, text, state):
        results =  [x for x in self.commands if x.startswith(text)] + [None]
        return results[state]

words = ["live", "song", "track", "clip", "device", "parameter", "parameters"]
completer = LiveAPICompleter(words)
readline.set_completer(completer.complete)

def print_error(address, args):
    print("Received error from Live: %s" % args)

def main(args):
    client = AbletonOSCClient(args.hostname, args.port)
    if args.verbose:
        client.verbose = True
    client.set_handler("/live/error", print_error)
    client.send_message("/live/api/reload")

    readline.parse_and_bind('tab: complete')
    print("AbletonOSC command console")
    print("Usage: /live/osc/command [params]")

    while True:
        try:
            command_str = input(">>> ")
        except EOFError:
            print()
            break

        if not re.search("\\w", command_str):
            #--------------------------------------------------------------------------------
            # Command is empty
            #--------------------------------------------------------------------------------
            continue
        if not re.search("^/", command_str):
            #--------------------------------------------------------------------------------
            # Command is invalid
            #--------------------------------------------------------------------------------
            print("OSC address must begin with a slash (/)")
            continue

        #--------------------------------------------------------------------------------
        # Parse command-line, with support for quoted strings
        #--------------------------------------------------------------------------------
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
    parser.add_argument("--port", type=str, default=11000)
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode: prints all OSC messages")
    args = parser.parse_args()
    main(args)
