from . import client, server, query_and_await, await_reply, wait_one_tick
import pytest

def test_track_get_volume(client, server):
    track_id = 2
    for value in [0.5, 1.0]:
        client.send_message("/live/track/set/volume", [track_id, value])
        assert query_and_await(client, server, "/live/track/get/volume", (track_id,),
                               lambda *params: params[0] == value)

def test_track_get_panning(client, server):
    track_id = 2
    for value in [0.5, 0.0]:
        client.send_message("/live/track/set/panning", [track_id, value])
        assert query_and_await(client, server, "/live/track/get/panning", (track_id,),
                               lambda *params: params[0] == value)

def test_track_get_send(client, server):
    track_id = 2
    send_id = 1

    for value in [0.5, 0.0]:
        client.send_message("/live/track/set/send", [track_id, send_id, value])
        assert query_and_await(client, server, "/live/track/get/send", (track_id, send_id),
                               lambda *params: params[0] == value)
