from . import client, wait_one_tick, silent_audio_file, remove_audio_file, TICK_DURATION
import time

def test_clip_slot_create_clips(client, silent_audio_file):
    try:
        # MIDI Clip
        assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, False)
        client.send_message("/live/clip_slot/create/midi_clip", (0, 0, 4.0))
        wait_one_tick()
        assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, True)
        
        # Audio Clip
        assert client.query("/live/clip_slot/get/has_clip", (2, 0)) == (2, 0, False)
        client.send_message("/live/clip_slot/create/audio_clip", (2, 0, str(silent_audio_file)))
        wait_one_tick()
        assert client.query("/live/clip_slot/get/has_clip", (2, 0)) == (2, 0, True)
        
    finally:
        client.send_message("/live/clip_slot/delete/clip", (0, 0))
        client.send_message("/live/clip_slot/delete/clip", (2, 0))
        remove_audio_file(silent_audio_file)
        wait_one_tick()
        
def test_clip_slot_create_clip_back_compat(client):
    try:
        # MIDI Clip
        assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, False)
        client.send_message("/live/clip_slot/create_clip", (0, 0, 4.0))
        wait_one_tick()
        assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, True)
        
    finally:
        client.send_message("/live/clip_slot/delete_clip", (0, 0))
        wait_one_tick()

def test_clip_slot_duplicate(client):
    try:
        client.send_message("/live/clip_slot/create/midi_clip", [0, 0, 4.0])
        client.send_message("/live/clip/get/notes", (0, 0))
        assert client.await_message("/live/clip/get/notes") == (0, 0)

        client.send_message("/live/clip/add/notes", (0, 0,
                                                    60, 0.0, 0.25, 64, False))

        client.send_message("/live/clip_slot/duplicate_to", (0, 0, 0, 2))
        client.send_message("/live/clip/get/notes", (0, 2))
        assert client.await_message("/live/clip/get/notes") == (0, 2,
                                                                60, 0.0, 0.25, 64, False)

    finally:
        client.send_message("/live/clip_slot/delete/clip", [0, 0])
        client.send_message("/live/clip_slot/delete/clip", [0, 2])
        wait_one_tick()

def test_clip_slot_fire_stop(client):
    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/set/clip_trigger_quantization", (0))
    try:
        client.send_message("/live/clip_slot/create/midi_clip", [0, 0, 4.0])
        # need delays since fire/stop doesn't trigger immediately
        client.send_message("/live/clip_slot/fire", (0, 0))
        wait_one_tick()
        assert client.query("/live/clip/get/is_playing", (0, 0)) == (0, 0, True)
        client.send_message("/live/clip_slot/stop", (0, 0))
        wait_one_tick()
        assert client.query("/live/clip/get/is_playing", (0, 0)) == (0, 0, False)
        client.send_message("/live/clip_slot/set/fire_button", (0, 0, 1))
        wait_one_tick()
        assert client.query("/live/clip/get/is_playing", (0, 0)) == (0, 0, True)
        client.send_message("/live/clip_slot/stop", (0, 0))  # set_fire_button_state to 0 does nothing.
    finally:
        client.send_message("/live/song/stop_playing")
        client.send_message("/live/clip_slot/delete/clip", [0, 0])
        wait_one_tick()


def test_clip_slot_property_listen(client):
    try:
        client.send_message("/live/clip_slot/start_listen/has_clip", (0, 0))
        assert client.await_message("/live/clip_slot/get/has_clip", TICK_DURATION * 2) == (0, 0, False)
        client.send_message("/live/clip_slot/create/midi_clip", [0, 0, 4.0])
        assert client.await_message("/live/clip_slot/get/has_clip", TICK_DURATION * 2) == (0, 0, True)
        client.send_message("/live/clip_slot/delete/clip", [0, 0])
        assert client.await_message("/live/clip_slot/get/has_clip", TICK_DURATION * 2) == (0, 0, False)
        client.send_message("/live/clip_slot/stop_listen/has_clip", (0, 0))
    finally:
        client.send_message("/live/clip_slot/delete/clip", [0, 0])
        wait_one_tick()

def _assert_clip_slot_get(client, prop, track_index=0, clip_index=0):
    rv = client.query(f"/live/clip_slot/get/{prop}", (track_index, clip_index))
    assert rv[0] == track_index and rv[1] == clip_index

def test_clip_slot_endpoints(client):
    client.send_message("/live/clip_slot/create/midi_clip", [0, 0, 4.0])

    try:
        # get read_only properties
        for prop in [
            "color",
            "color_index",
            "controls_other_clips",
            "has_clip",
            "has_stop_button",
            "is_group_slot",
            "is_playing",
            "is_recording",
            "is_triggered",
            "playing_status",
            "will_record_on_start",
        ]:
            _assert_clip_slot_get(client, prop, 0, 0)

        # set has_stop_button (rw property)
        client.send_message("/live/clip_slot/set/has_stop_button", (0, 0, 1))
        assert client.query("/live/clip_slot/get/has_stop_button", (0, 0)) == (0, 0, True)
        client.send_message("/live/clip_slot/set/has_stop_button", (0, 0, 0))
        assert client.query("/live/clip_slot/get/has_stop_button", (0, 0)) == (0, 0, False)

        # check listeners are created
        for prop in [
            "color",
            "color_index",
            "controls_other_clips",
            "has_clip",
            "has_stop_button",
            "is_triggered",
            "playing_status",
        ]:
            client.send_message(f"/live/clip_slot/start_listen/{prop}", (0, 0))
            rv = client.await_message(f"/live/clip_slot/get/{prop}", TICK_DURATION * 2)
            assert rv[0] == 0 and rv[1] == 0
            client.send_message(f"/live/clip_slot/stop_listen/{prop}", (0, 0))

    finally:
        client.send_message("/live/clip_slot/delete/clip", [0, 0])
        wait_one_tick()
