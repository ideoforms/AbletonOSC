from . import client, wait_one_tick, silent_audio_file, TICK_DURATION
import pytest
import itertools
import math

#--------------------------------------------------------------------------------
# Test track properties
#--------------------------------------------------------------------------------

def _test_track_property(client, track_id, property, values=None):
    if values is None:
        rv = client.query("/live/track/get/%s" % property, [track_id])
        assert rv[0] == track_id
        assert len(rv) >= 2
        return
    for value in values:
        print("Testing property %s, value: %s" % (property, value))
        client.send_message("/live/track/set/%s" % property, [track_id, value])
        wait_one_tick()
        assert client.query("/live/track/get/%s" % property, [track_id]) == (track_id, value,)

@pytest.mark.parametrize(
    "property,values",
    [
        # Only specific colors from the color picker can be used
        ("color", [0x001AFF2F, 0x001A2F96]),
        ("color_index", [1, 2]),
        ("arm", [1, 0]),
        ("current_monitoring_state", [0, 1]),
        ("back_to_arranger", [0]),
        ("implicit_arm", [1, 0]),
        ("mute", [1, 0]),
        ("solo", [1, 0]),
        ("name", ["Test", "Track"]),
    ],
)
def test_track_properties_get_set(client, property, values):
    _test_track_property(client, 2, property, values)

@pytest.mark.parametrize(
    "property",
    [
        "can_be_armed",
        "can_be_frozen",
        "can_show_chains",
        "fired_slot_index",
        "has_audio_input",
        "has_audio_output",
        "has_midi_input",
        "has_midi_output",
        "input_meter_level",
        "input_meter_left",
        "input_meter_right",
        "fold_state",  # Group tracks only
        "is_foldable",
        "is_frozen",
        "is_grouped",
        "is_part_of_selection",
        "is_showing_chains",  # Group tracks only
        "is_visible",
        "muted_via_solo",
        "output_meter_level",
        "output_meter_left",
        "output_meter_right",
        "playing_slot_index",
    ],
)
def test_track_properties_get_only(client, property):
    _test_track_property(client, 2, property, None)

@pytest.mark.parametrize(
    "property,values",
    [
        ("panning", [0.5, 0.0]),
        ("volume", [0.5, 1.0]),
        ("track_activator", [1, 0]),
        ("left_split_stereo", [-0.5, 0.5]),
        ("right_split_stereo", [-0.5, 0.5]),
        ("crossfade_assign", [0, 2]),
        ("panning_mode", [0, 1]),
    ],
)
def test_track_mixer_properties(client, property, values):
    _test_track_property(client, 2, property, values)

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
# Test track properties - routing
#--------------------------------------------------------------------------------

def _test_track_routing_current(client, track_id, property):
    rv = client.query("/live/track/get/%s" % property, [track_id])
    assert rv[0] == track_id
    if len(rv) < 2 or rv[1] in (None, ""):
        return
    client.send_message("/live/track/set/%s" % property, [track_id, rv[1]])
    wait_one_tick()
    assert client.query("/live/track/get/%s" % property, [track_id]) == (track_id, rv[1],)

@pytest.mark.parametrize(
    "property",
    [
        "input_routings",
        "input_sub_routings",
        "output_routings",
        "output_sub_routings",
    ],
)
def test_track_routing_lists(client, property):
    track_id = 2
    rv = client.query("/live/track/get/%s" % property, [track_id])
    assert rv[0] == track_id

@pytest.mark.parametrize(
    "property",
    [
        "current_input_routing",
        "current_input_sub_routing",
        "current_output_routing",
        "current_output_sub_routing",
    ],
)
def test_track_routing_current(client, property):
    track_id = 2
    _test_track_routing_current(client, track_id, property)

#--------------------------------------------------------------------------------
# Test track view properties
#--------------------------------------------------------------------------------

def _toggle_view_property(client, track_id, prop):
    msg = client.query("/live/track/view/get/%s" % prop, (track_id,))
    assert msg[0] == track_id
    current = msg[1]
    if current in (0, 1, True, False):
        new_value = 0 if current else 1
    else:
        new_value = current
    client.send_message("/live/track/view/set/%s" % prop, (track_id, new_value))
    wait_one_tick()
    msg = client.query("/live/track/view/get/%s" % prop, (track_id,))
    assert msg == (track_id, new_value)

def test_track_view_properties(client):
    track_id = 2
    msg = client.query("/live/track/view/get/device_insert_mode", (track_id,))
    assert msg[0] == track_id
    _toggle_view_property(client, track_id, "is_collapsed")

#--------------------------------------------------------------------------------
# Test track properties - clips
#--------------------------------------------------------------------------------

def test_track_midi_clips(client):
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

    client.send_message("/live/track/delete_clip", (track_id, 0))
    client.send_message("/live/track/delete_clip", (track_id, 1))

def test_track_audio_clips(client, silent_audio_file):
    track_id = 2
    client.send_message("/live/clip_slot/create/audio_clip", (track_id, 0, str(silent_audio_file)))
    client.send_message("/live/clip_slot/create/audio_clip", (track_id, 1, str(silent_audio_file)))
    client.send_message("/live/clip/set/name", (track_id, 0, "Alpha"))
    client.send_message("/live/clip/set/name", (track_id, 1, "Beta"))

    wait_one_tick()
    names = client.query("/live/track/get/clips/name", (track_id,))
    lengths = client.query("/live/track/get/clips/length", (track_id,))
    assert names[:3] == (track_id, "Alpha", "Beta")
    assert lengths[0] == track_id
    assert lengths[1] is not None
    assert lengths[2] is not None

    client.send_message("/live/clip_slot/delete_clip", (track_id, 0))
    client.send_message("/live/clip_slot/delete_clip", (track_id, 1))

#--------------------------------------------------------------------------------
# Test track methods - duplicate clip to arrangement
#--------------------------------------------------------------------------------

def test_track_duplicate_clip_to_arrangement(client):
    track_id = 0
    clip_id = 0
    start_time = 0.0
    client.send_message("/live/clip_slot/create/midi_clip", (track_id, clip_id, 4.0))
    client.send_message("/live/clip/set/name", (track_id, clip_id, "Alpha"))
    wait_one_tick()

    client.send_message("/live/track/duplicate/clip_to_arrangement", (track_id, clip_id, start_time))
    wait_one_tick()

    names = client.query("/live/track/get/arrangement_clips/name", (track_id,))
    times = client.query("/live/track/get/arrangement_clips/start_time", (track_id,))
    assert "Alpha" in names[1:]
    assert any(t is not None and math.isclose(t, start_time, abs_tol=1e-4) for t in times[1:])

    client.send_message("/live/clip_slot/delete_clip", (track_id, clip_id))
    client.send_message("/live/track/delete/arrangement_clip", (track_id, clip_id))

#--------------------------------------------------------------------------------
# Test track methods - duplicate clip slot
#--------------------------------------------------------------------------------

def test_track_duplicate_clip_slot(client):
    track_id = 0
    source_clip_id = 0
    target_clip_id = 1
    try:
        client.send_message("/live/clip_slot/create_clip", (track_id, source_clip_id, 4.0))
        wait_one_tick()
        client.send_message("/live/clip/set/name", (track_id, source_clip_id, "Alpha"))
        wait_one_tick()

        client.send_message("/live/track/duplicate/clip_slot", (track_id, source_clip_id))
        wait_one_tick()

        name = client.query("/live/clip/get/name", (track_id, target_clip_id))
        assert name == (track_id, target_clip_id, "Alpha")
    finally:
        client.send_message("/live/clip_slot/delete_clip", (track_id, source_clip_id))
        client.send_message("/live/clip_slot/delete_clip", (track_id, target_clip_id))

#--------------------------------------------------------------------------------
# Test track methods - create arrangment clips
#--------------------------------------------------------------------------------

def test_track_create_arrangement_midi_clip(client):
    track_id = 0
    start_time = 0.0
    length = 4.0
    try:
        client.send_message("/live/track/create/midi_clip", (track_id, start_time, length))
        wait_one_tick()
        times = client.query("/live/track/get/arrangement_clips/start_time", (track_id,))[1:]
        lengths = client.query("/live/track/get/arrangement_clips/length", (track_id,))[1:]
        assert any(t is not None and math.isclose(t, start_time, abs_tol=1e-4) for t in times)
        assert any(l is not None and math.isclose(l, length, abs_tol=1e-4) for l in lengths)
    finally:
        times = client.query("/live/track/get/arrangement_clips/start_time", (track_id,))[1:]
        for i, t in enumerate(times):
            if t is not None and math.isclose(t, start_time, abs_tol=1e-4):
                client.send_message("/live/track/delete/arrangement_clip", (track_id, i))
                break

#--------------------------------------------------------------------------------
# Test track methods - jump in running session clip
#--------------------------------------------------------------------------------

def test_track_jump_in_running_session_clip(client):
    track_id = 0
    clip_id = 0
    try:
        client.send_message("/live/clip_slot/create_clip", (track_id, clip_id, 4.0))
        client.send_message("/live/clip_slot/fire", (track_id, clip_id))
        wait_one_tick()
        client.send_message("/live/track/jump_in_running_session_clip", (track_id, 0.5))
        wait_one_tick()
    finally:
        client.send_message("/live/clip_slot/delete_clip", (track_id, clip_id))

def test_track_create_arrangement_audio_clip(client, silent_audio_file):
    track_id = 2
    start_time = 2.0
    try:
        client.send_message("/live/track/create/audio_clip", (track_id, str(silent_audio_file), start_time))
        wait_one_tick()
        times = client.query("/live/track/get/arrangement_clips/start_time", (track_id,))[1:]
        assert any(t is not None and math.isclose(t, start_time, abs_tol=1e-4) for t in times)
    finally:
        times = client.query("/live/track/get/arrangement_clips/start_time", (track_id,))[1:]
        for i, t in enumerate(times):
            if t is not None and math.isclose(t, start_time, abs_tol=1e-4):
                client.send_message("/live/track/delete/arrangement_clip", (track_id, i))
                break


#--------------------------------------------------------------------------------
# Test track properties - devices
#--------------------------------------------------------------------------------

def test_track_devices(client):
    track_id = 0
    assert client.query("/live/track/get/num_devices", (track_id,)) == (track_id, 0,)

#--------------------------------------------------------------------------------
# Test track properties - listeners
#--------------------------------------------------------------------------------

def test_track_listen_playing_slot_index(client):
    # 1/16th quantize
    try:
        client.send_message("/live/song/set/clip_trigger_quantization", (11,))
        for track_id, clip_id in itertools.product((0, 1), (0, 1)):
            client.send_message("/live/clip_slot/create_clip", (track_id, clip_id, 4))

        # -2 = Clip Stop slot fired; -1 = arrangement recording with no session clip playing
        # Depending on test order, either may be returned.
        client.send_message("/live/track/start_listen/playing_slot_index", (0,))
        msg = client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2)
        assert msg[0] == 0 and msg[1] in (-1, -2)
        client.send_message("/live/track/start_listen/playing_slot_index", (1,))
        msg = client.await_message("/live/track/get/playing_slot_index", TICK_DURATION * 2)
        assert msg[0] == 1 and msg[1] in (-1, -2)

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

    finally:
        for track_id, clip_id in itertools.product((0, 1), (0, 1)):
            client.send_message("/live/clip_slot/delete_clip", (track_id, clip_id))
        client.send_message("/live/song/stop_playing")
    
    
