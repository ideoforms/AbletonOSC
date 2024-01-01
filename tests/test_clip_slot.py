from . import client, wait_one_tick, TICK_DURATION

def test_clip_slot_has_clip(client):
    assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, False)
    client.send_message("/live/clip_slot/create_clip", (0, 0, 4.0))
    assert client.query("/live/clip_slot/get/has_clip", (0, 0)) == (0, 0, True)
    client.send_message("/live/clip_slot/delete_clip", (0, 0))

def test_clip_slot_duplicate(client):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 4.0])
    client.send_message("/live/clip/get/notes", (0, 0))
    assert client.await_message("/live/clip/get/notes") == (0, 0)

    client.send_message("/live/clip/add/notes", (0, 0,
                                                 60, 0.0, 0.25, 64, False))

    client.send_message("/live/clip_slot/duplicate_clip_to", (0, 0, 0, 2))
    client.send_message("/live/clip/get/notes", (0, 2))
    assert client.await_message("/live/clip/get/notes") == (0, 2,
                                                            60, 0.0, 0.25, 64, False)

    client.send_message("/live/clip_slot/delete_clip", [0, 0])
    client.send_message("/live/clip_slot/delete_clip", [0, 2])

def test_clip_slot_property_listen(client):
    client.send_message("/live/clip_slot/start_listen/has_clip", (0, 0))
    assert client.await_message("/live/clip_slot/get/has_clip", TICK_DURATION * 2) == (0, 0, False)
    client.send_message("/live/clip_slot/create_clip", [0, 0, 4.0])
    assert client.await_message("/live/clip_slot/get/has_clip", TICK_DURATION * 2) == (0, 0, True)
    client.send_message("/live/clip_slot/delete_clip", [0, 0])
    assert client.await_message("/live/clip_slot/get/has_clip", TICK_DURATION * 2) == (0, 0, False)
    client.send_message("/live/clip_slot/stop_listen/has_clip", (0,))