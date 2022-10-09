from . import client, server, query_and_await, await_reply, wait_one_tick

#--------------------------------------------------------------------------------
# Test clip properties
#--------------------------------------------------------------------------------

def _test_clip_property(client, server, track_id, clip_id, property, values):
    for value in values:
        print("Testing clip property %s, value: %s" % (property, value))
        client.send_message("/live/clip/set/%s" % property, [track_id, clip_id, value])
        wait_one_tick()
        assert query_and_await(client, server, "/live/clip/get/%s" % property, (track_id, clip_id),
                               fn=lambda *params: params[0] == value)

def test_clip_property_name(client, server):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 4.0])
    _test_clip_property(client, server, 0, 0, "name", ["Alpha", "Beta"])
    client.send_message("/live/clip_slot/delete_clip", [0, 0])

def test_clip_property_color(client, server):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 4.0])
    _test_clip_property(client, server, 0, 0, "color", [0x001AFF2F, 0x001A2F96])
    client.send_message("/live/clip_slot/delete_clip", [0, 0])

def test_clip_add_notes(client, server):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 4.0])
    wait_one_tick()
    client.send_message("/live/clip/add_new_note", [0, 0, 60, 0.0, 0.25, 64, False])
    client.send_message("/live/clip/add_new_note", [0, 0, 67, 0.25, 0.5, 32, False])

    def check_notes(*params):
        assert params[:5] == (60, 0.0, 0.25, 64, False)
        assert params[5:10] == (67, 0.25, 0.5, 32, False)
        return True

    client.send_message("/live/clip/get/notes", [0, 0])
    assert await_reply(server, "/live/clip/get/notes", check_notes)
    client.send_message("/live/clip_slot/delete_clip", [0, 0])
