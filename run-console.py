#!/usr/bin/env python3

#--------------------------------------------------------------------------------
# Console client for AbletonOSC.
# Takes OSC commands and parameters, and prints the return value.
#--------------------------------------------------------------------------------

import argparse
import readline

from client import AbletonOSCClient

def main(args):
    client = AbletonOSCClient(args.hostname, args.port)
    client.send_message("/live/reload")

    readline.parse_and_bind('tab: complete')
    print("AbletonOSC command console")
    print("Usage: /live/osc/command [params]")

    while True:
        try:
            command_str = input(">>> ")
        except EOFError:
            print()
            break
        command, *params_str = command_str.split(" ")
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
            print(client.query(command, params))
        except RuntimeError:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Console client for AbletonOSC. Takes OSC commands and parameters, and prints the return value.")
    parser.add_argument("--hostname", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=str, default=11000)
    args = parser.parse_args()
    main(args)
