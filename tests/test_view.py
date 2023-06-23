from . import client, wait_one_tick

#--------------------------------------------------------------------------------
# Test view features
#--------------------------------------------------------------------------------

def test_selected_scene(client):
    client.send_message("/live/view/set/selected_scene", (1, ))
    rv = client.query("/live/view/get/selected_scene")
    assert rv == (1, )

def test_selected_track(client):
    client.send_message("/live/view/set/selected_track", (2, ))
    rv = client.query("/live/view/get/selected_track")
    assert rv == (2, )

def test_selected_clip(client):
    client.send_message("/live/view/set/selected_clip", (3, 4))
    rv = client.query("/live/view/get/selected_clip")
    assert rv == (3, 4)