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
    midi_track_id = 0
    midi_clip_id = 0
    client.send_message("/live/clip_slot/create_clip", [midi_track_id, midi_clip_id, 4.0])

    audio_track_id = 2
    audio_clip_id = 0
    client.send_message("/live/track/set/arm", [audio_track_id, True])
    client.send_message("/live/clip_slot/fire", [audio_track_id, audio_clip_id])
    wait_one_tick()
    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/stop_all_clips")
    client.send_message("/live/track/set/arm", [audio_track_id, False])
    yield
    client.send_message("/live/track/delete_clip", [audio_track_id, audio_clip_id])
    client.send_message("/live/track/delete_clip", [midi_track_id, midi_clip_id])

#--------------------------------------------------------------------------------
# Test clip properties
#--------------------------------------------------------------------------------

def _test_clip_property(client, track_id, clip_id, property, values):
    for value in values:
        print("Testing clip property %s, value: %s" % (property, value))
        client.send_message("/live/clip/set/%s" % property, (track_id, clip_id, value))
        wait_one_tick()
        assert client.query("/live/clip/get/%s" % property, (track_id, clip_id)) == (track_id, clip_id, value,)

def test_clip_property_name(client):
    _test_clip_property(client, 0, 0, "name", ("Alpha", "Beta"))

def test_clip_property_color(client):
    _test_clip_property(client, 0, 0, "color", (0x001AFF2F, 0x001A2F96))

def test_clip_property_gain(client):
    _test_clip_property(client, 2, 0, "gain", (0.5, 1.0))

def test_clip_property_pitch_coarse(client):
    _test_clip_property(client, 2, 0, "pitch_coarse", (4, 0))

def test_clip_property_pitch_fine(client):
    _test_clip_property(client, 2, 0, "pitch_fine", (0.5, 0.0))

def test_clip_add_notes(client):
    client.send_message("/live/clip/get/notes", (0, 0))
    assert client.await_message("/live/clip/get/notes") == (0, 0)

    client.send_message("/live/clip/add/notes", (0, 0,
                                                 60, 0.0, 0.25, 64, False,
                                                 67, 0.25, 0.5, 32, False))

    client.send_message("/live/clip/get/notes", (0, 0))
    assert client.await_message("/live/clip/get/notes") == (0, 0,
                                                            60, 0.0, 0.25, 64, False,
                                                            67, 0.25, 0.5, 32, False)
