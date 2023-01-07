from . import client, wait_one_tick

def test_clip_slot_has_clip(client):
    assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, False)
    client.send_message("/live/clip_slot/create_clip", (0, 0, 4.0))
    assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, True)
    client.send_message("/live/clip_slot/delete_clip", (0, 0))
