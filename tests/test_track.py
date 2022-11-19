from . import client, wait_one_tick, TICK_DURATION
import pytest

def test_track_get_send(client):
    track_id = 2
    send_id = 1

    for value in [0.5, 0.0]:
        client.send_message("/live/track/set/send", [track_id, send_id, value])
        wait_one_tick()
        assert client.query("/live/track/get/send", (track_id, send_id)) == (value,)

#--------------------------------------------------------------------------------
# Test track properties
#--------------------------------------------------------------------------------

def _test_track_property(client, track_id, property, values):
    for value in values:
        print("Testing property %s, value: %s" % (property, value))
        client.send_message("/live/track/set/%s" % property, [track_id, value])
        wait_one_tick()
        assert client.query("/live/track/get/%s" % property, [track_id]) == (value,)

def test_track_property_panning(client):
    _test_track_property(client, 2, "panning", [0.5, 0.0])

def test_track_property_volume(client):
    _test_track_property(client, 2, "volume", [0.5, 1.0])

def test_track_property_color(client):
    # Only specific colors from the color picker can be used
    _test_track_property(client, 2, "color", [0x001AFF2F, 0x001A2F96])

def test_track_property_mute(client):
    _test_track_property(client, 2, "mute", [1, 0])

def test_track_property_solo(client):
    _test_track_property(client, 2, "solo", [1, 0])

def test_track_property_name(client):
    _test_track_property(client, 2, "name", ["Test", "Track"])

#--------------------------------------------------------------------------------
# Test track properties - clips
#--------------------------------------------------------------------------------

def test_track_clips(client):
    track_id = 0
    client.send_message("/live/clip_slot/create_clip", (track_id, 0, 4))
    client.send_message("/live/clip_slot/create_clip", (track_id, 1, 2))
    client.send_message("/live/clip/set/name", (track_id, 0, "Alpha"))
    client.send_message("/live/clip/set/name", (track_id, 1, "Beta"))

    wait_one_tick()
    assert client.query("/live/track/get/clips/name", (track_id,)) == ("Alpha", "Beta")
    assert client.query("/live/track/get/clips/length", (track_id,)) == (4, 2)

    client.send_message("/live/clip_slot/delete_clip", (track_id, 0))
    client.send_message("/live/clip_slot/delete_clip", (track_id, 1))

#--------------------------------------------------------------------------------
# Test track properties - devices
#--------------------------------------------------------------------------------

def test_track_devices(client):
    track_id = 0
    assert client.query("/live/track/get/num_devices", (track_id,)) == (0,)

#--------------------------------------------------------------------------------
# Test track properties - listeners
#--------------------------------------------------------------------------------

def test_track_listen_playing_slot_index(client):
    track_id = 0
    # 1/16th quantize
    client.send_message("/live/song/set/clip_trigger_quantization", (11,))
    client.send_message("/live/clip_slot/create_clip", (track_id, 0, 4))
    client.send_message("/live/clip_slot/create_clip", (track_id, 1, 4))

    client.send_message("/live/track/start_listen/playing_slot_index", (track_id,))
    client.send_message("/live/clip_slot/fire", (track_id, 0))
    assert client.await_reply("/live/track/get/playing_slot_index", lambda params: params[0] == 0, TICK_DURATION * 2)
    client.send_message("/live/clip_slot/fire", (track_id, 1))
    assert client.await_reply("/live/track/get/playing_slot_index", lambda params: params[0] == 1, TICK_DURATION * 2)
    client.send_message("/live/track/stop_listen/playing_slot_index", (track_id,))

    client.send_message("/live/clip_slot/delete_clip", (track_id, 0))
    client.send_message("/live/clip_slot/delete_clip", (track_id, 1))