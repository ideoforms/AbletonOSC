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
# /live/track/create_midi_clip and /live/track/create_audio_clip exercise the
# arrangement-view clip creation surface of the Live API. They do not affect
# the session view — that surface is served by /live/clip_slot/create_clip.
#
# These tests use /live/song/undo to roll back state after each create, so the
# test set is left as it was found.
#--------------------------------------------------------------------------------

def test_track_create_midi_clip_in_arrangement(client):
    track_id = 0
    start_time, end_time = 0.0, 4.0

    initial = client.query("/live/track/get/arrangement_clips/name", (track_id,))

    client.send_message("/live/track/create_midi_clip", (track_id, start_time, end_time))
    wait_one_tick()

    after = client.query("/live/track/get/arrangement_clips/name", (track_id,))
    # (track_id,) is the response prefix; after the new clip there must be one
    # more entry than before.
    assert len(after) == len(initial) + 1, \
        "Expected arrangement clip count to grow by 1; before=%s after=%s" % (initial, after)

    # Undo to clean up — create_midi_clip is undoable per the LOM contract.
    client.send_message("/live/song/undo", ())
    wait_one_tick()

def test_track_create_audio_clip_in_arrangement(client, tmp_path):
    """Generate a one-second silent WAV on disk and import it as an arrangement
    audio clip onto track 2 (the default test audio track). Undo afterwards."""
    import wave
    wav_path = tmp_path / "abletonosc_test_silence.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b"\x00\x00" * 44100)

    track_id = 2
    position = 0.0

    initial = client.query("/live/track/get/arrangement_clips/name", (track_id,))

    client.send_message("/live/track/create_audio_clip",
                        (track_id, str(wav_path), position))
    wait_one_tick()

    after = client.query("/live/track/get/arrangement_clips/name", (track_id,))
    assert len(after) == len(initial) + 1, \
        "Expected arrangement clip count to grow by 1; before=%s after=%s" % (initial, after)

    client.send_message("/live/song/undo", ())
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
