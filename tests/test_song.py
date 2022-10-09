from . import client, server, query_and_await, await_reply, wait_one_tick

#--------------------------------------------------------------------------------
# Test song start/stop
#--------------------------------------------------------------------------------

def test_song_play(client, server):
    client.send_message("/live/song/start_playing", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/is_playing", (),
                           lambda *params: params[0] is True)

    client.send_message("/live/song/stop_playing", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/is_playing", (),
                           lambda *params: params[0] is False)

def test_song_beat(client, server):
    client.send_message("/live/song/stop_playing", [])
    client.send_message("/live/song/start_playing", [])
    assert await_reply(server, "/live/song/beat", lambda *params: params[0] == 0, timeout=1.0)
    assert await_reply(server, "/live/song/beat", lambda *params: params[0] == 1, timeout=1.0)
    assert await_reply(server, "/live/song/beat", lambda *params: params[0] == 2, timeout=1.0)
    client.send_message("/live/song/stop_playing", [])
    wait_one_tick()
    client.send_message("/live/song/continue_playing", [])
    assert await_reply(server, "/live/song/beat", lambda *params: params[0] == 3, timeout=1.0)
    client.send_message("/live/song/stop_playing", [])

def test_song_stop_all_clips(client, server):
    client.send_message("/live/clip_slot/create_clip", (0, 0, 4))
    client.send_message("/live/clip_slot/create_clip", (1, 0, 4))
    client.send_message("/live/clip/fire", (0, 0))
    client.send_message("/live/clip/fire", (1, 0))
    # Sometimes a wait >one tick is required here. Not sure why.
    wait_one_tick()
    wait_one_tick()
    assert query_and_await(client, server, "/live/clip/get/is_playing", (0, 0), lambda *params: params[0] is True)
    assert query_and_await(client, server, "/live/clip/get/is_playing", (1, 0), lambda *params: params[0] is True)

    client.send_message("/live/song/stop_playing", [])
    client.send_message("/live/song/stop_all_clips", [])
    wait_one_tick()
    wait_one_tick()
    assert query_and_await(client, server, "/live/clip/get/is_playing", (0, 0), lambda *params: params[0] is False)
    assert query_and_await(client, server, "/live/clip/get/is_playing", (1, 0), lambda *params: params[0] is False)

    client.send_message("/live/clip_slot/delete_clip", (0, 0))
    client.send_message("/live/clip_slot/delete_clip", (1, 0))

#--------------------------------------------------------------------------------
# Test song properties
#--------------------------------------------------------------------------------

def _test_song_property(client, server, property, values):
    for value in values:
        print("Testing property %s, value: %s" % (property, value))
        client.send_message("/live/song/set/%s" % property, [value])
        wait_one_tick()
        assert query_and_await(client, server, "/live/song/get/%s" % property,
                               fn=lambda *params: params[0] == value)

def test_song_property_arrangement_overdub(client, server):
    _test_song_property(client, server, "arrangement_overdub", [1, 0])

def test_song_property_back_to_arranger(client, server):
    # Can't really test back_to_arranger without making some modifications
    # in the arrangement view to reset (it's not possible to set back_to_arranger = 1)
    _test_song_property(client, server, "back_to_arranger", [0])

def test_song_property_clip_trigger_quantization(client, server):
    _test_song_property(client, server, "clip_trigger_quantization", [0, 4])

def test_song_property_current_song_time(client, server):
    _test_song_property(client, server, "current_song_time", [4, 1])

def test_song_property_groove_amount(client, server):
    _test_song_property(client, server, "groove_amount", [0.5, 0])

def test_song_property_loop(client, server):
    _test_song_property(client, server, "loop", [1, 0])

def test_song_property_loop_length(client, server):
    _test_song_property(client, server, "loop_length", [2, 4])

def test_song_property_loop_start(client, server):
    _test_song_property(client, server, "loop_start", [2, 1])

def test_song_property_metronome(client, server):
    _test_song_property(client, server, "metronome", [1, 0])

def test_song_property_midi_recording_quantization(client, server):
    _test_song_property(client, server, "midi_recording_quantization", [1, 0])

def test_song_property_nudge_down(client, server):
    _test_song_property(client, server, "nudge_down", [1, 0])

def test_song_property_nudge_up(client, server):
    _test_song_property(client, server, "nudge_up", [1, 0])

def test_song_property_punch_in(client, server):
    _test_song_property(client, server, "punch_in", [1, 0])

def test_song_property_punch_out(client, server):
    _test_song_property(client, server, "punch_out", [1, 0])

def test_song_property_record_mode(client, server):
    _test_song_property(client, server, "record_mode", [1, 0])
    client.send_message("/live/song/stop_playing", [])

def test_song_property_tempo(client, server):
    _test_song_property(client, server, "tempo", [125.5, 120])

#--------------------------------------------------------------------------------
# Test song properties - tracks
#--------------------------------------------------------------------------------

def test_song_tracks(client, server):
    assert query_and_await(client, server, "/live/song/get/num_tracks",
                           fn=lambda *params: params[0] == 4)
    client.send_message("/live/song/create_midi_track", [-1])
    wait_one_tick()
    wait_one_tick()
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/num_tracks",
                           fn=lambda *params: params[0] == 5)
    client.send_message("/live/song/delete_track", [4])
    wait_one_tick()
    wait_one_tick()
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/num_tracks",
                           fn=lambda *params: params[0] == 4)


#--------------------------------------------------------------------------------
# Test song properties - scenes
#--------------------------------------------------------------------------------

def test_song_scenes(client, server):
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 8)
    client.send_message("/live/song/create_scene", [-1])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 9)
    client.send_message("/live/song/delete_scene", [8])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 8)

def test_song_duplicate_scene(client, server):
    track_id = 0
    scene_id = 7
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 8)

    client.send_message("/live/clip_slot/create_clip", [track_id, scene_id, 4])
    client.send_message("/live/song/duplicate_scene", [scene_id])
    wait_one_tick()
    assert query_and_await(client, server, "/live/clip/get/is_midi_clip", (track_id, scene_id + 1),
                           fn=lambda *params: params[0] is True)
    client.send_message("/live/song/delete_scene", [scene_id + 1])
    client.send_message("/live/clip_slot/delete_clip", [0, scene_id])

#--------------------------------------------------------------------------------
# Test song - undo/redo
#--------------------------------------------------------------------------------

def test_song_undo_redo(client, server):
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 8)
    client.send_message("/live/song/create_scene", [-1])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 9)

    wait_one_tick()
    client.send_message("/live/song/undo", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 8)

    client.send_message("/live/song/redo", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/num_scenes",
                           fn=lambda *params: params[0] == 9)
    client.send_message("/live/song/delete_scene", [8])