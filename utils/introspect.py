#!/usr/bin/env python3
"""
Generic introspection tool for Ableton Live objects via AbletonOSC.

This utility allows you to discover all available properties and methods on any
Live object that has an introspection endpoint implemented.

Usage:
    ./utils/introspect.py device <track_id> <device_id>
    ./utils/introspect.py clip <track_id> <clip_id>
    ./utils/introspect.py track <track_id>
    ./utils/introspect.py song

Examples:
    # Introspect first device on track 0
    ./utils/introspect.py device 0 0

    # Introspect first clip on track 2
    ./utils/introspect.py clip 2 0

    # Introspect track 1
    ./utils/introspect.py track 1

    # Introspect song object
    ./utils/introspect.py song

Requirements:
    - Ableton Live must be running
    - AbletonOSC must be loaded as a Control Surface
    - The introspection endpoint must be implemented for the object type

Note:
    Currently, only /live/device/introspect is implemented.
    This tool is designed to be extensible as more introspection endpoints are added.
"""

import sys
import argparse
import socket
from pathlib import Path

# Add parent directory to path to import client
sys.path.insert(0, str(Path(__file__).parent.parent))
from client.client import AbletonOSCClient

# Mapping of object types to their introspection endpoints
INTROSPECTION_ENDPOINTS = {
    "device": "/live/device/introspect",
    # Future endpoints can be added here:
    # "clip": "/live/clip/introspect",
    # "track": "/live/track/introspect",
    # "song": "/live/song/introspect",
}

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

def format_introspection_output(result, object_type, object_ids):
    """Format and print the introspection results in a readable way."""
    if not result or len(result) < 3:
        print(f"❌ No introspection data received for {object_type} {object_ids}")
        return

    # Parse the result
    current_section = None
    properties = []
    methods = []

    for item in result[len(object_ids):]:  # Skip object IDs
        if item == "PROPERTIES:":
            current_section = "properties"
        elif item == "METHODS:":
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
        # Highlight interesting keywords
        interesting_keywords = ['variation', 'macro', 'chain', 'selected', 'current', 'active']
        interesting_props = [p for p in properties if any(k in p.lower() for k in interesting_keywords)]
        other_props = [p for p in properties if p not in interesting_props]

        if interesting_props:
            print("\n🎯 HIGHLIGHTED (variation, macro, chain, selected, etc.):")
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
        interesting_keywords = ['variation', 'macro', 'chain', 'recall', 'store', 'delete']
        interesting_methods = [m for m in methods if any(k in m.lower() for k in interesting_keywords)]

        if interesting_methods:
            print("\n🎯 HIGHLIGHTED (variation, macro, chain, recall, etc.):")
            for method in sorted(interesting_methods):
                print(f"  ✨ {method}()")

        print(f"\n📝 ALL METHODS ({len(methods)} total):")
        for method in sorted(methods):
            print(f"  • {method}()")
    else:
        print("  (No methods found)")

    print()
    print("=" * 80)

def introspect_object(object_type, object_ids, client_port=None):
    """
    Introspect a Live object and print its properties and methods.

    Args:
        object_type: Type of object (device, clip, track, song)
        object_ids: List of IDs to identify the object (e.g., [track_id, device_id])
        client_port: Optional client port to use
    """
    # Check if introspection is implemented for this object type
    if object_type not in INTROSPECTION_ENDPOINTS:
        print(f"❌ Error: Introspection not yet implemented for '{object_type}'")
        print()
        print("Currently supported object types:")
        for obj_type in INTROSPECTION_ENDPOINTS.keys():
            print(f"  • {obj_type}")
        print()
        print("To add support for more object types, implement the corresponding")
        print("introspection handler in the AbletonOSC server code.")
        return False

    endpoint = INTROSPECTION_ENDPOINTS[object_type]

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
        # Query the introspection endpoint
        result = client.query(endpoint, object_ids)
        format_introspection_output(result, object_type, object_ids)
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

    success = introspect_object(args.object_type, args.object_ids, args.port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
