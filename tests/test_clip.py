from . import client, wait_one_tick, TICK_DURATION
import pytest
import random

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
    client.send_message("/live/clip_slot/create_clip", [midi_track_id, midi_clip_id, 8.0])

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

def test_clip_add_remove_notes(client):
    assert client.query("/live/clip/get/notes", (0, 0)) == (0, 0)

    client.send_message("/live/clip/add/notes", (0, 0,
                                                 60, 0.0, 0.25, 64, False,
                                                 67, -0.25, 0.5, 32, False))

    # Should return all notes, including those before time = 0
    assert client.query("/live/clip/get/notes", (0, 0)) == (0, 0,
                                                            60, 0.0, 0.25, 64, False,
                                                            67, -0.25, 0.5, 32, False)

    client.send_message("/live/clip/add/notes", (0, 0,
                                                 72, 0.0, 0.25, 64, False,
                                                 60, 3.0, 0.5, 32, False))

    # Query between t in [0..2] and pitch in [60, 71]
    # Should only return a single note
    assert client.query("/live/clip/get/notes", (0, 0, 60, 11, 0, 2)) == (0, 0,
                                                                          60, 0.0, 0.25, 64, False)

    client.send_message("/live/clip/remove/notes", (0, 0, 60, 11, 0, 2))
    assert client.query("/live/clip/get/notes", (0, 0)) == (0, 0,
                                                            60, 3.0, 0.5, 32, False,
                                                            67, -0.25, 0.5, 32, False,
                                                            72, 0.0, 0.25, 64, False)
    client.send_message("/live/clip/remove/notes", (0, 0))
    assert client.query("/live/clip/get/notes", (0, 0)) == (0, 0)

def test_clip_add_many_notes(client):
    """
    Test adding large numbers of notes to a clip.
    Note that Ableton API's get_notes returns notes sorted by pitch, then time, so add notes
    in this same order.
    """
    random.seed(0)
    all_note_data = []
    pitch = 0
    for pitch_index in range(127):
        time = random.randrange(-32, 32) / 4
        duration = random.randrange(1, 4) / 4
        velocity = random.randrange(1, 128)
        # Create multiple instances of the same sequence, shifted in time.
        for timeshift in range(3):
            note = (pitch,
                    time + (timeshift * 8),
                    duration,
                    velocity,
                    False)
            all_note_data += note
        pitch += 1
    all_note_data = tuple(all_note_data)

    # Check clip is initially empty
    assert client.query("/live/clip/get/notes", (0, 0)) == (0, 0)

    # Populate clip and check return value
    client.send_message("/live/clip/add/notes", (0, 0) + all_note_data)
    assert client.query("/live/clip/get/notes", (0, 0)) == (0, 0) + all_note_data

    # Clear clip
    client.send_message("/live/clip/remove/notes", (0, 0))

def test_clip_playing_position_listen(client):
    client.send_message("/live/clip/start_listen/playing_position", [0, 0])
    client.send_message("/live/clip/fire", [0, 0])

    rv = client.await_message("/live/clip/get/playing_position", TICK_DURATION * 2)
    assert rv == (0, 0, 0)

    rv = client.await_message("/live/clip/get/playing_position", TICK_DURATION * 2)
    assert rv[0] == 0
    assert rv[1] == 0
    assert rv[2] > 0

    client.send_message("/live/clip/stop_listen/playing_position", (0, 0))

def test_clip_listen_lifecycle(client):
    client.send_message("/live/clip/set/name", [0, 0, "Alpha"])
    wait_one_tick()
    client.send_message("/live/clip/start_listen/name", [0, 0])
    assert client.await_message("/live/clip/get/name", TICK_DURATION * 2) == (0, 0, "Alpha")
    client.send_message("/live/clip/set/name", [0, 0, "Beta"])
    assert client.await_message("/live/clip/get/name", TICK_DURATION * 2) == (0, 0, "Beta")

    client.send_message("/live/clip_slot/delete_clip", [0, 0])
    client.send_message("/live/clip_slot/create_clip", [0, 0, 8.0])
    client.send_message("/live/clip/start_listen/name", [0, 0])
    assert client.await_message("/live/clip/get/name", TICK_DURATION * 2) == (0, 0, "")
    client.send_message("/live/clip/set/name", [0, 0, "Alpha"])
    assert client.await_message("/live/clip/get/name", TICK_DURATION * 2) == (0, 0, "Alpha")
    client.send_message("/live/clip/stop_listen/name", [0, 0])