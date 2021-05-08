from . import client, server, query_and_await, await_reply, wait_one_tick

def test_clip_add_notes(client, server):
    client.send_message("/live/clip_slot/delete_clip", [0, 0])
    client.send_message("/live/clip_slot/create_clip", [0, 0, 4.0])
    wait_one_tick()
    client.send_message("/live/clip/add_new_note", [0, 0, 0.0, 0.25, 60, 64, False])
    client.send_message("/live/clip/add_new_note", [0, 0, 0.25, 0.5, 67, 32, False])

    def check_notes(_, *params):
        # For some reason, get_notes has a different order to set_notes
        assert params[:5] == (60, 0.0, 0.25, 62, False)
        assert params[5:10] == (67, 0.25, 0.5, 32, False)
        return True

    client.send_message("/live/clip/get/notes", [0, 0])
    assert await_reply(server, "/live/clip/get/notes", check_notes)
