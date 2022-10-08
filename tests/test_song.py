from . import client, server, query_and_await, await_reply, wait_one_tick

def test_song_play(client, server):
    client.send_message("/live/song/start_playing", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/is_playing", (),
                           lambda *params: params[0] is True)

    client.send_message("/live/song/stop_playing", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/is_playing", (),
                           lambda *params: params[0] is False)

def _test_song_property(client, server, property, values):
    for value in values:
        print("Testing property %s, value: %s" % (property, value))
        client.send_message("/live/song/set/%s" % property, [value])
        wait_one_tick()
        assert query_and_await(client, server, "/live/song/get/%s" % property,
                               fn=lambda *params: params[0] == value)

def test_song_property_tempo(client, server):
    _test_song_property(client, server, "tempo", [125.5, 120])

def test_song_property_metronome(client, server):
    _test_song_property(client, server, "metronome", [1, 0])

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
