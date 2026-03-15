from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test song start/stop
#--------------------------------------------------------------------------------

def test_song_play(client):
    client.send_message("/live/song/start_playing")
    wait_one_tick()
    assert client.query("/live/song/get/is_playing") == (True,)

    client.send_message("/live/song/stop_playing")
    wait_one_tick()
    assert client.query("/live/song/get/is_playing") == (False,)

def test_song_beat(client):
    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/start_listen/beat")
    client.send_message("/live/song/start_playing")
    wait_one_tick()
    wait_one_tick()
    assert client.await_message("/live/song/get/beat", timeout=1.0) == (1,)
    assert client.await_message("/live/song/get/beat", timeout=1.0) == (2,)
    client.send_message("/live/song/stop_playing")
    wait_one_tick()
    client.send_message("/live/song/continue_playing")
    assert client.await_message("/live/song/get/beat", timeout=1.0) == (3,)
    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/stop_listen/beat")
    wait_one_tick()

def test_song_stop_all_clips(client):
    client.send_message("/live/clip_slot/create_clip", (0, 0, 4))
    client.send_message("/live/clip_slot/create_clip", (1, 0, 4))
    client.send_message("/live/clip/fire", (0, 0))
    client.send_message("/live/clip/fire", (1, 0))
    # Sometimes a wait >one tick is required here. Not sure why.
    wait_one_tick()
    wait_one_tick()
    assert client.query("/live/clip/get/is_playing", (0, 0)) == (0, 0, True,)
    assert client.query("/live/clip/get/is_playing", (1, 0)) == (1, 0, True,)

    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/stop_all_clips")
    wait_one_tick()
    wait_one_tick()
    assert client.query("/live/clip/get/is_playing", (0, 0)) == (0, 0, False,)
    assert client.query("/live/clip/get/is_playing", (1, 0)) == (1, 0, False,)

    client.send_message("/live/clip_slot/delete_clip", (0, 0))
    client.send_message("/live/clip_slot/delete_clip", (1, 0))

#--------------------------------------------------------------------------------
# Test song listeners
#--------------------------------------------------------------------------------

def test_song_listen_is_playing(client):
    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/start_listen/is_playing")
    assert client.await_message("/live/song/get/is_playing", TICK_DURATION * 2) == (False,)
    client.send_message("/live/song/start_playing")
    assert client.await_message("/live/song/get/is_playing", TICK_DURATION * 2) == (True,)
    client.send_message("/live/song/stop_playing")
    assert client.await_message("/live/song/get/is_playing", TICK_DURATION * 2) == (False,)
    client.send_message("/live/song/stop_listen/is_playing")

def test_song_listen_tempo(client):
    client.send_message("/live/song/set/tempo", [120])
    client.send_message("/live/song/start_listen/tempo")
    assert client.await_message("/live/song/get/tempo", TICK_DURATION * 2) == (120,)

    for value in [81, 120]:
        client.send_message("/live/song/set/tempo", [value])
        assert client.await_message("/live/song/get/tempo", TICK_DURATION * 2) == (value,)

    client.send_message("/live/song/stop_listen/tempo")

#--------------------------------------------------------------------------------
# Test song properties
#--------------------------------------------------------------------------------

def _test_song_property(client, property, values):
    for value in values:
        client.send_message("/live/song/set/%s" % property, [value])
        wait_one_tick()
        assert client.query("/live/song/get/%s" % property) == (value,)

def test_song_property_arrangement_overdub(client):
    _test_song_property(client, "arrangement_overdub", [1, 0])

def test_song_property_back_to_arranger(client):
    # Can't really test back_to_arranger without making some modifications
    # in the arrangement view to reset (it's not possible to set back_to_arranger = 1)
    _test_song_property(client, "back_to_arranger", [0])

def test_song_property_clip_trigger_quantization(client):
    _test_song_property(client, "clip_trigger_quantization", [0, 4])

def test_song_property_current_song_time(client):
    _test_song_property(client, "current_song_time", [4, 1])

def test_song_property_groove_amount(client):
    _test_song_property(client, "groove_amount", [0.5, 0])

def test_song_property_loop(client):
    _test_song_property(client, "loop", [1, 0])

def test_song_property_loop_length(client):
    _test_song_property(client, "loop_length", [2, 4])

def test_song_property_loop_start(client):
    _test_song_property(client, "loop_start", [2, 1])

def test_song_property_metronome(client):
    _test_song_property(client, "metronome", [1, 0])

def test_song_property_midi_recording_quantization(client):
    _test_song_property(client, "midi_recording_quantization", [1, 0])

def test_song_property_nudge_down(client):
    _test_song_property(client, "nudge_down", [1, 0])

def test_song_property_nudge_up(client):
    _test_song_property(client, "nudge_up", [1, 0])

def test_song_property_punch_in(client):
    _test_song_property(client, "punch_in", [1, 0])

def test_song_property_punch_out(client):
    _test_song_property(client, "punch_out", [1, 0])

def test_song_property_record_mode(client):
    _test_song_property(client, "record_mode", [1, 0])
    client.send_message("/live/song/stop_playing")

def test_song_property_tempo(client):
    _test_song_property(client, "tempo", [125.5, 120])

#--------------------------------------------------------------------------------
# Test song properties - tracks
#--------------------------------------------------------------------------------

def test_song_tracks(client):
    assert client.query("/live/song/get/num_tracks") == (4,)
    client.send_message("/live/song/create_midi_track", [-1])
    wait_one_tick()
    wait_one_tick()
    wait_one_tick()
    assert client.query("/live/song/get/num_tracks") == (5,)
    client.send_message("/live/song/delete_track", [4])
    wait_one_tick()
    wait_one_tick()
    wait_one_tick()
    assert client.query("/live/song/get/num_tracks") == (4,)

#--------------------------------------------------------------------------------
# Test song properties - scenes
#--------------------------------------------------------------------------------

def test_song_scenes(client):
    assert client.query("/live/song/get/num_scenes") == (8,)
    client.send_message("/live/song/create_scene", [-1])
    wait_one_tick()
    assert client.query("/live/song/get/num_scenes") == (9,)
    client.send_message("/live/song/delete_scene", [8])
    wait_one_tick()
    assert client.query("/live/song/get/num_scenes") == (8,)

def test_song_duplicate_scene(client):
    track_id = 0
    scene_id = 7
    assert client.query("/live/song/get/num_scenes") == (8,)

    client.send_message("/live/clip_slot/create_clip", [track_id, scene_id, 4])
    client.send_message("/live/song/duplicate_scene", [scene_id])
    wait_one_tick()
    assert client.query("/live/clip/get/is_midi_clip", (track_id, scene_id + 1)) == (track_id, scene_id + 1, True,)
    client.send_message("/live/song/delete_scene", [scene_id + 1])
    client.send_message("/live/clip_slot/delete_clip", [0, scene_id])

#--------------------------------------------------------------------------------
# Test song - undo/redo
#--------------------------------------------------------------------------------

def test_song_undo_redo(client):
    assert client.query("/live/song/get/num_scenes") == (8,)
    client.send_message("/live/song/create_scene", [-1])
    wait_one_tick()
    assert client.query("/live/song/get/num_scenes") == (9,)

    wait_one_tick()
    client.send_message("/live/song/undo")
    wait_one_tick()
    assert client.query("/live/song/get/num_scenes") == (8,)

    client.send_message("/live/song/redo")
    wait_one_tick()
    assert client.query("/live/song/get/num_scenes") == (9,)
    client.send_message("/live/song/delete_scene", [8])

#--------------------------------------------------------------------------------
# Test song - track names with master/return tracks
#--------------------------------------------------------------------------------

def test_song_get_track_names_no_params_includes_main_and_returns(client):
    """No params: should return all regular tracks + master + return tracks."""
    result = client.query("/live/song/get/track_names")
    # 4 regular tracks + Master + at least one return track (A)
    assert len(result) > 4
    # Master track name should be present
    assert "Main" in result

def test_song_get_track_names_open_ended_includes_main_and_returns(client):
    """Range ending in -1: should include master and return tracks."""
    result = client.query("/live/song/get/track_names", (0, -1))
    assert "Main" in result

def test_song_get_track_names_explicit_range_excludes_main_and_returns(client):
    """Explicit numeric range: should include only regular tracks, no master/returns."""
    result = client.query("/live/song/get/track_names", (0, 2))
    assert len(result) == 2
    assert "Main" not in result

def test_song_get_track_names_partial_open_ended_includes_main_and_returns(client):
    """Range starting mid-list, ending at -1: includes remaining regular tracks + master + returns."""
    result = client.query("/live/song/get/track_names", (2, -1))
    assert "Main" in result

#--------------------------------------------------------------------------------
# Test song - track data with master/return tracks
#--------------------------------------------------------------------------------

def test_song_get_track_data_open_ended_includes_main_and_returns(client):
    """track_data with -1 range should include master and return track names."""
    result = client.query("/live/song/get/track_data", (0, -1, "track.name"))
    assert result is not None
    assert "Main" in result

def test_song_get_track_data_explicit_range_excludes_main(client):
    """track_data with explicit range should not include master track name."""
    result = client.query("/live/song/get/track_data", (0, 2, "track.name"))
    assert result is not None
    assert "Main" not in result

def test_song_get_track_data_clip_property_with_master_does_not_crash(client):
    """
    Querying a clip property across the full range (including master/return tracks
    that have no clip_slots) should not raise an error - master/returns return None.
    """
    result = client.query("/live/song/get/track_data", (0, -1, "clip.name"))
    assert result is not None

def test_song_get_track_data_clip_slot_property_with_master_does_not_crash(client):
    """
    Querying a clip_slot property across the full range should not raise for
    master/return tracks that have no clip_slots.
    """
    result = client.query("/live/song/get/track_data", (0, -1, "clip_slot.has_clip"))
    assert result is not None

def test_song_get_track_data_device_property_with_master(client):
    """
    Querying a device property across the full range (including master/return tracks)
    should not crash. Master/return tracks with no devices yield an empty contribution.
    """
    result = client.query("/live/song/get/track_data", (0, -1, "device.name"))
    assert result is not None
