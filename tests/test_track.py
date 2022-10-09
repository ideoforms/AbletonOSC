from . import client, server, query_and_await, await_reply, wait_one_tick
import pytest

def test_track_get_send(client, server):
    track_id = 2
    send_id = 1

    for value in [0.5, 0.0]:
        client.send_message("/live/track/set/send", [track_id, send_id, value])
        assert query_and_await(client, server, "/live/track/get/send", (track_id, send_id),
                               lambda *params: params[0] == value)

#--------------------------------------------------------------------------------
# Test track properties
#--------------------------------------------------------------------------------

def _test_track_property(client, server, track_id, property, values):
    for value in values:
        print("Testing property %s, value: %s" % (property, value))
        client.send_message("/live/track/set/%s" % property, [track_id, value])
        wait_one_tick()
        assert query_and_await(client, server, "/live/track/get/%s" % property, [track_id],
                               fn=lambda *params: params[0] == value)

def test_track_property_panning(client, server):
    _test_track_property(client, server, 2, "panning", [0.5, 0.0])

def test_track_property_volume(client, server):
    _test_track_property(client, server, 2, "volume", [0.5, 1.0])

def test_track_property_color(client, server):
    # Only specific colors from the color picker can be used
    _test_track_property(client, server, 2, "color", [0x001AFF2F, 0x001A2F96])

def test_track_property_mute(client, server):
    _test_track_property(client, server, 2, "mute", [1, 0])

def test_track_property_solo(client, server):
    _test_track_property(client, server, 2, "solo", [1, 0])

def test_track_property_name(client, server):
    _test_track_property(client, server, 2, "name", ["Test", "Track"])
