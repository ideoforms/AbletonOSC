#!/usr/bin/env python3
"""
Generic introspection tool for Ableton Live objects via AbletonOSC.

This utility allows you to discover all available properties and methods on any
Live object that has an introspection endpoint implemented.

Usage:
    ./devel/introspect.py device <track_id> <device_id>
    ./devel/introspect.py clip <track_id> <clip_id>
    ./devel/introspect.py track <track_id>
    ./devel/introspect.py song

Examples:
    # Introspect first device on track 0
    ./devel/introspect.py device 0 0

    # Introspect first clip on track 2
    ./devel/introspect.py clip 2 0

    # Introspect track 1
    ./devel/introspect.py track 1

    # Introspect song object
    ./devel/introspect.py song

Requirements:
    - Ableton Live must be running
    - AbletonOSC must be loaded as a Control Surface
    - The introspection endpoint must be implemented for the object type

"""

import sys
import argparse
import socket
from pathlib import Path

# Add parent directory to path to import client
sys.path.insert(0, str(Path(__file__).parent.parent))
from client.client import AbletonOSCClient

# Introspection endpoint (unified for all object types)
INTROSPECTION_ENDPOINT = "/live/introspect"

def find_free_port(start_port=11001, max_attempts=10):
    """Find a free UDP port for the OSC client."""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

def format_introspection_output(result, object_type, object_ids, highlight_keywords=None):
    """Format and print the introspection results in a readable way.

    Args:
        result: The introspection data received from the server
        object_type: Type of object being introspected
        object_ids: IDs used to identify the object
        highlight_keywords: Optional list of keywords to highlight in the output
    """
    if not result or len(result) < 3:
        print(f"❌ No introspection data received for {object_type} {object_ids}")
        return

    # Parse the result
    current_section = None
    properties = []
    methods = []

    for item in result[len(object_ids):]:  # Skip object IDs
        if item == "properties:":
            current_section = "properties"
        elif item == "methods:":
            current_section = "methods"
        elif current_section == "properties":
            properties.append(item)
        elif current_section == "methods":
            methods.append(item)

    # Print header
    print("=" * 80)
    print(f"INTROSPECTION: {object_type.upper()} {' '.join(map(str, object_ids))}")
    print("=" * 80)
    print()

    # Print properties
    print("📋 PROPERTIES:")
    print("-" * 80)
    if properties:
        # Highlight if keywords provided
        if highlight_keywords:
            interesting_props = [p for p in properties if any(k in p.lower() for k in highlight_keywords)]

            if interesting_props:
                print(f"\n🎯 HIGHLIGHTED ({', '.join(highlight_keywords)}):")
                for prop in sorted(interesting_props):
                    print(f"  ✨ {prop}")

        print(f"\n📝 ALL PROPERTIES ({len(properties)} total):")
        for prop in sorted(properties):
            print(f"  • {prop}")
    else:
        print("  (No properties found)")

    print()

    # Print methods
    print("🔧 METHODS:")
    print("-" * 80)
    if methods:
        # Highlight if keywords provided
        if highlight_keywords:
            interesting_methods = [m for m in methods if any(k in m.lower() for k in highlight_keywords)]

            if interesting_methods:
                print(f"\n🎯 HIGHLIGHTED ({', '.join(highlight_keywords)}):")
                for method in sorted(interesting_methods):
                    print(f"  ✨ {method}()")

        print(f"\n📝 ALL METHODS ({len(methods)} total):")
        for method in sorted(methods):
            print(f"  • {method}()")
    else:
        print("  (No methods found)")

    print()
    print("=" * 80)

def introspect_object(object_type, object_ids, client_port=None, highlight_keywords=None):
    """
    Introspect a Live object and print its properties and methods.

    Args:
        object_type: Type of object (device, clip, track, song)
        object_ids: List of IDs to identify the object (e.g., [track_id, device_id])
        client_port: Optional client port to use
        highlight_keywords: Optional list of keywords to highlight in the output
    """
    # Validate object type
    valid_types = ["device", "clip", "track", "song"]
    if object_type not in valid_types:
        print(f"❌ Error: Unknown object type '{object_type}'")
        print()
        print("Supported object types:")
        for obj_type in valid_types:
            print(f"  • {obj_type}")
        return False

    # Find a free port if not specified
    if client_port is None:
        client_port = find_free_port()
        if client_port is None:
            print("❌ Unable to find a free UDP port.")
            return False

    # Connect to AbletonOSC
    try:
        client = AbletonOSCClient(client_port=client_port)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print()
        print("⚠️  Make sure:")
        print("   1. Ableton Live is running")
        print("   2. AbletonOSC is loaded as a Control Surface")
        print()
        return False

    try:
        # Query the introspection endpoint with object_type as first parameter
        params = (object_type,) + tuple(object_ids)
        result = client.query(INTROSPECTION_ENDPOINT, params)
        format_introspection_output(result, object_type, object_ids, highlight_keywords)
        return True
    except Exception as e:
        print(f"❌ Introspection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.stop()

def main():
    parser = argparse.ArgumentParser(
        description="Introspect Ableton Live objects via AbletonOSC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s device 0 0           Introspect device 0 on track 0
  %(prog)s device 2 1           Introspect device 1 on track 2
  %(prog)s clip 0 0             Introspect clip in slot 0 on track 0
  %(prog)s track 1              Introspect track 1
  %(prog)s song                 Introspect the song object

Note: Currently only 'device' introspection is implemented.
      Other object types will be added as introspection endpoints are created.
        """
    )

    parser.add_argument(
        "object_type",
        choices=["device", "clip", "track", "song"],
        help="Type of Live object to introspect"
    )

    parser.add_argument(
        "object_ids",
        nargs="*",
        type=int,
        help="Object IDs (e.g., track_id device_id for devices)"
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Client port to use (default: auto-detect free port)"
    )

    parser.add_argument(
        "--highlight",
        type=str,
        help="Comma-separated keywords to highlight in the output (e.g., 'variation,macro,chain')"
    )

    args = parser.parse_args()

    # Validate object IDs based on object type
    expected_ids = {
        "device": 2,  # track_id, device_id
        "clip": 2,    # track_id, clip_id
        "track": 1,   # track_id
        "song": 0,    # no IDs needed
    }

    expected = expected_ids.get(args.object_type, 0)
    if len(args.object_ids) != expected:
        print(f"❌ Error: '{args.object_type}' requires {expected} ID(s), got {len(args.object_ids)}")
        if expected > 0:
            id_names = {
                "device": "track_id device_id",
                "clip": "track_id clip_id",
                "track": "track_id",
            }
            print(f"   Usage: {sys.argv[0]} {args.object_type} {id_names.get(args.object_type)}")
        sys.exit(1)

    # Parse highlight keywords if provided
    highlight_keywords = None
    if args.highlight:
        highlight_keywords = [kw.strip().lower() for kw in args.highlight.split(',')]

    success = introspect_object(args.object_type, args.object_ids, args.port, highlight_keywords)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
