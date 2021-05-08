from . import client, server, query_and_await, await_reply, wait_one_tick

def test_song_tempo_get(client, server):
    client.send_message("/live/song/set/tempo", [120.0])
    assert query_and_await(client, server, "/live/song/get/tempo",
                           lambda _, *params: params[0] == 120.0)
    client.send_message("/live/song/set/tempo", [125.0])
    assert query_and_await(client, server, "/live/song/get/tempo",
                           lambda _, *params: params[0] == 125.0)

def test_song_start_playing(client, server):
    client.send_message("/live/song/start_playing", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/is_playing",
                           lambda _, *params: params[0] is True)

    client.send_message("/live/song/stop_playing", [])
    wait_one_tick()
    assert query_and_await(client, server, "/live/song/get/is_playing",
                           lambda _, *params: params[0] is False)

def test_song_beat(client, server):
    client.send_message("/live/song/stop_playing", [])
    client.send_message("/live/song/start_playing", [])
    assert await_reply(server, "/live/song/beat", lambda _, *params: params[0] == 0, timeout=1.0)
    assert await_reply(server, "/live/song/beat", lambda _, *params: params[0] == 1, timeout=1.0)
    assert await_reply(server, "/live/song/beat", lambda _, *params: params[0] == 2, timeout=1.0)
    client.send_message("/live/song/stop_playing", [])
