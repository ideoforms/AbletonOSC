from . import client, wait_one_tick
import pytest

#--------------------------------------------------------------------------------
# To test clips, initialise by creating an empty MIDI clip and recording
# a short segment of audio.
#
# Note that for these tests to succeed, a default audio input device must be set.
#--------------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def _create_test_clips(client):
    track_id = 0
    clip_id = 0
    client.send_message("/live/clip_slot/create_clip", [track_id, clip_id, 4.0])

    track_id = 2
    clip_id = 0
    client.send_message("/live/track/set/arm", [track_id, True])
    client.send_message("/live/clip_slot/fire", [track_id, clip_id])
    wait_one_tick()
    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/stop_all_clips")
    client.send_message("/live/track/set/arm", [track_id, False])
    yield
    client.send_message("/live/track/delete_clip", [track_id, clip_id])

#--------------------------------------------------------------------------------
# Test clip properties
#--------------------------------------------------------------------------------

def _test_clip_property(client, track_id, clip_id, property, values):
    for value in values:
        print("Testing clip property %s, value: %s" % (property, value))
        client.send_message("/live/clip/set/%s" % property, [track_id, clip_id, value])
        wait_one_tick()
        assert client.query_and_await("/live/clip/get/%s" % property, (track_id, clip_id),
                                      fn=lambda params: params[0] == value)

def test_clip_property_name(client):
    _test_clip_property(client, 0, 0, "name", ["Alpha", "Beta"])

def test_clip_property_color(client):
    _test_clip_property(client, 0, 0, "color", [0x001AFF2F, 0x001A2F96])

def test_clip_property_gain(client):
    _test_clip_property(client, 2, 0, "gain", [0.5, 1.0])

def test_clip_property_pitch_coarse(client):
    _test_clip_property(client, 2, 0, "pitch_coarse", [4, 0])

def test_clip_property_pitch_fine(client):
    _test_clip_property(client, 2, 0, "pitch_fine", [0.5, 0.0])

def test_clip_add_notes(client):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 4.0])
    wait_one_tick()
    client.send_message("/live/clip/add/notes", [0, 0, 60, 0.0, 0.25, 64, False])
    client.send_message("/live/clip/add/notes", [0, 0, 67, 0.25, 0.5, 32, False])

    def check_notes(params):
        assert params[:5] == (60, 0.0, 0.25, 64, False)
        assert params[5:10] == (67, 0.25, 0.5, 32, False)
        return True

    client.send_message("/live/clip/get/notes", [0, 0])
    assert client.await_reply("/live/clip/get/notes", check_notes)
    client.send_message("/live/clip_slot/delete_clip", [0, 0])
