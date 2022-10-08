from . import client, server, query_and_await, await_reply, wait_one_tick
import pytest

def test_track_get_volume(client, server):
    client.send_message("/live/track/set/volume", [2, 0.5])

    assert query_and_await(client, server, "/live/track/get/volume", (2,),
                           lambda *params: params[0] == pytest.approx(0.5, rel=0.00001))
