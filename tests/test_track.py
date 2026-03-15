from . import client, wait_one_tick, TICK_DURATION
import pytest
import itertools

#--------------------------------------------------------------------------------
# Test track properties
#--------------------------------------------------------------------------------

def _test_track_property(client, track_id, property, values):
    for value in values:
        print("Testing property %s, value: %s" % (property, value))
        client.send_message("/live/track/set/%s" % property, [track_id, value])
        wait_one_tick()
        assert client.query("/live/track/get/%s" % property, [track_id]) == (track_id, value,)

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
# Test track properties - sends
#--------------------------------------------------------------------------------

def test_track_get_send(client):
    track_id = 2
    send_id = 1

    for value in [0.5, 0.0]:
        client.send_message("/live/track/set/send", [track_id, send_id, value])
        wait_one_tick()
        assert client.query("/live/track/get/send", (track_id, send_id)) == (track_id, send_id, value,)

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
    assert client.query("/live/track/get/clips/name", (track_id,)) == (track_id,
                                                                       "Alpha", "Beta", None, None,
                                                                       None, None, None, None)
    assert client.query("/live/track/get/clips/length", (track_id,)) == (track_id,
                                                                         4, 2, None, None,
                                                                         None, None, None, None)

    client.send_message("/live/clip_slot/delete_clip", (track_id, 0))
    client.send_message("/live/clip_slot/delete_clip", (track_id, 1))

#--------------------------------------------------------------------------------
# Test track properties - devices
#--------------------------------------------------------------------------------

def test_track_devices(client):
    track_id = 0
    assert client.query("/live/track/get/num_devices", (track_id,)) == (track_id, 0,)

#--------------------------------------------------------------------------------
# Test track properties - master track
#--------------------------------------------------------------------------------

def test_track_master_get_name(client):
    result = client.query("/live/track/get/name", ("master",))
    assert result[0] == "master"
    assert result[1] == "Main"

def test_track_main_alias(client):
    result_master = client.query("/live/track/get/name", ("master",))
    result_main = client.query("/live/track/get/name", ("main",))
    assert result_master[0] == "master"
    assert result_main[0] == "master"
    assert result_master[1] == result_main[1]

def test_track_master_volume(client):
    client.send_message("/live/track/set/volume", ("master", 0.5))
    wait_one_tick()
    assert client.query("/live/track/get/volume", ("master",)) == ("master", 0.5)
    client.send_message("/live/track/set/volume", ("master", 1.0))
    wait_one_tick()

def test_track_master_num_devices(client):
    result = client.query("/live/track/get/num_devices", ("master",))
    assert result[0] == "master"
    assert isinstance(result[1], int)

#--------------------------------------------------------------------------------
# Test track properties - return tracks
#--------------------------------------------------------------------------------

def test_track_return_get_name(client):
    result = client.query("/live/track/get/name", ("A",))
    assert result is not None
    assert result[0] == "A"

def test_track_return_volume(client):
    client.send_message("/live/track/set/volume", ("A", 0.5))
    wait_one_tick()
    assert client.query("/live/track/get/volume", ("A",)) == ("A", 0.5)
    client.send_message("/live/track/set/volume", ("A", 1.0))
    wait_one_tick()


def test_track_return_num_devices(client):
    result = client.query("/live/track/get/num_devices", ("A",))
    assert result[0] == "A"
    assert isinstance(result[1], int)

#--------------------------------------------------------------------------------
# Test that numeric indices still work (regression)
#--------------------------------------------------------------------------------

def test_track_numeric_index_regression(client):
    result = client.query("/live/track/get/name", (0,))
    assert result[0] == 0
    assert isinstance(result[1], str)

def test_track_numeric_index_volume_regression(client):
    client.send_message("/live/track/set/volume", (2, 0.5))
    wait_one_tick()
    assert client.query("/live/track/get/volume", (2,)) == (2, 0.5)
    client.send_message("/live/track/set/volume", (2, 1.0))
    wait_one_tick()

#--------------------------------------------------------------------------------
# Test listeners - master track
#--------------------------------------------------------------------------------

def test_track_listen_master_volume(client):
    client.send_message("/live/track/set/volume", ("master", 1.0))
    client.send_message("/live/track/start_listen/volume", ("master",))
    assert client.await_message("/live/track/get/volume", TICK_DURATION * 2) == ("master", 1.0)

    client.send_message("/live/track/set/volume", ("master", 0.5))
    assert client.await_message("/live/track/get/volume", TICK_DURATION * 2) == ("master", 0.5)

    client.send_message("/live/track/stop_listen/volume", ("master",))
    client.send_message("/live/track/set/volume", ("master", 1.0))
    wait_one_tick()

#--------------------------------------------------------------------------------
# Test track properties - listeners
#--------------------------------------------------------------------------------

def test_track_listen_playing_slot_index(client):
    # 1/16th quantize
    client.send_message("/live/song/set/clip_trigger_quantization", (11,))
    for track_id, clip_id in itertools.product((0, 1), (0, 1)):
        client.send_message("/live/clip_slot/create_clip", (track_id, clip_id, 4))

    client.send_message("/live/track/start_listen/playing_slot_index", (0,))
    assert client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2) == (0, -1,)
    client.send_message("/live/track/start_listen/playing_slot_index", (1,))
    assert client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2) == (1, -1,)

    client.send_message("/live/clip_slot/fire", (0, 0))
    assert client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2) == (0, 0,)

    client.send_message("/live/clip_slot/fire", (0, 1))
    assert client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2) == (0, 1,)

    client.send_message("/live/clip_slot/fire", (1, 1))
    assert client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2) == (1, 1,)

    client.send_message("/live/clip_slot/fire", (1, 0))
    assert client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2) == (1, 0,)

    client.send_message("/live/track/stop_listen/playing_slot_index", (0,))
    client.send_message("/live/track/stop_listen/playing_slot_index", (1,))

    for track_id, clip_id in itertools.product((0, 1), (0, 1)):
        client.send_message("/live/clip_slot/delete_clip", (track_id, clip_id))
