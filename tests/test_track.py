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
# Master track addressing — both "master" and the "main" alias should resolve
# to the same track, properties should round-trip, and the response identifier
# must come back as the canonical "master" string.
#--------------------------------------------------------------------------------

def test_track_master_get_name(client):
    result = client.query("/live/track/get/name", ("master",))
    assert result[0] == "master"
    assert isinstance(result[1], str) and len(result[1]) > 0

def test_track_main_alias_matches_master(client):
    result_master = client.query("/live/track/get/name", ("master",))
    result_main = client.query("/live/track/get/name", ("main",))
    # Both forms must resolve to the master track and echo "master" as the canonical id.
    assert result_master[0] == "master"
    assert result_main[0] == "master"
    assert result_master[1] == result_main[1]

def test_track_master_volume_roundtrip(client):
    client.send_message("/live/track/set/volume", ("master", 0.5))
    wait_one_tick()
    assert client.query("/live/track/get/volume", ("master",)) == ("master", 0.5)
    # Restore so we don't leave the fixture in a surprising state.
    client.send_message("/live/track/set/volume", ("master", 1.0))
    wait_one_tick()

def test_track_master_num_devices(client):
    result = client.query("/live/track/get/num_devices", ("master",))
    assert result[0] == "master"
    assert isinstance(result[1], int)

def test_track_master_clip_endpoints_return_empty(client):
    # The master track has no clip_slots — clip-list endpoints should return an
    # empty tuple body rather than crashing on the missing attribute.
    result = client.query("/live/track/get/clips/name", ("master",))
    assert result == ("master",)

def test_track_listen_master_volume(client):
    client.send_message("/live/track/set/volume", ("master", 1.0))
    wait_one_tick()
    client.send_message("/live/track/start_listen/volume", ("master",))
    assert client.await_message("/live/track/get/volume", TICK_DURATION * 2) == ("master", 1.0)

    client.send_message("/live/track/set/volume", ("master", 0.5))
    assert client.await_message("/live/track/get/volume", TICK_DURATION * 2) == ("master", 0.5)

    client.send_message("/live/track/stop_listen/volume", ("master",))
    client.send_message("/live/track/set/volume", ("master", 1.0))
    wait_one_tick()

#--------------------------------------------------------------------------------
# Return track addressing — same set of checks, plus verification that the
# letter-label form ("return_A") resolves to the same track as the numeric
# form ("return_0") and echoes the canonical "return_0" identifier.
#
# These tests assume the default Live set contains at least one return track,
# which is the standard template. If a custom default set removes all returns
# they will fail with an IndexError from _resolve_track — expected behaviour.
#--------------------------------------------------------------------------------

def test_track_return_numeric_and_letter_aliases_match(client):
    result_numeric = client.query("/live/track/get/name", ("return_0",))
    result_letter = client.query("/live/track/get/name", ("return_A",))
    assert result_numeric[0] == "return_0"
    assert result_letter[0] == "return_0"
    assert result_numeric[1] == result_letter[1]

def test_track_return_volume_roundtrip(client):
    client.send_message("/live/track/set/volume", ("return_0", 0.5))
    wait_one_tick()
    assert client.query("/live/track/get/volume", ("return_0",)) == ("return_0", 0.5)
    client.send_message("/live/track/set/volume", ("return_0", 1.0))
    wait_one_tick()

def test_track_return_num_devices(client):
    result = client.query("/live/track/get/num_devices", ("return_0",))
    assert result[0] == "return_0"
    assert isinstance(result[1], int)

#--------------------------------------------------------------------------------
# Regression — int track indices must keep working exactly as before so that
# this change doesn't break clients that were written before string IDs existed.
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
# Song-level master/return endpoints
#--------------------------------------------------------------------------------

def test_song_master_track_name(client):
    result = client.query("/live/song/get/master_track_name", ())
    assert len(result) == 1
    assert isinstance(result[0], str) and len(result[0]) > 0

def test_song_num_return_tracks(client):
    result = client.query("/live/song/get/num_return_tracks", ())
    assert len(result) == 1
    assert isinstance(result[0], int)
    assert result[0] >= 0

def test_song_return_track_names(client):
    result = client.query("/live/song/get/return_track_names", ())
    # Each element should be a string. Length matches num_return_tracks.
    num = client.query("/live/song/get/num_return_tracks", ())[0]
    assert len(result) == num
    for name in result:
        assert isinstance(name, str)

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
