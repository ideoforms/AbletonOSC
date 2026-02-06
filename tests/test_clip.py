from client.client import TICK_DURATION
from . import client, silent_audio_file, wait_one_tick


# -----------------------------------------------------------------------------
# Test playback controls
# -----------------------------------------------------------------------------

def test_clip_playback_controls(client):
    track_id = 0
    clip_id = 0

    client.send_message("/live/clip_slot/create_clip", [track_id, clip_id, 8.0])

    try:
        # Add a couple notes so the clip has content
        client.send_message("/live/clip/add/notes", (track_id, clip_id,
                                                     60, 0.0, 0.5, 100, False,
                                                     64, 0.5, 0.5, 100, False))
        wait_one_tick()


        # Fire
        client.send_message("/live/clip/fire", (track_id, clip_id))
        wait_one_tick()
        is_playing = client.query("/live/clip/get/is_playing", (track_id, clip_id))[2]
        assert bool(is_playing)
        
        # Move playing position forward while playing
        client.send_message("/live/clip/move/playing_pos", (track_id, clip_id, 4.0))
        wait_one_tick()
        playing_pos = client.query("/live/clip/get/playing_position", (track_id, clip_id))[2]
        assert playing_pos >= 3.5
        
        # Stop
        client.send_message("/live/clip/stop", (track_id, clip_id))
        wait_one_tick()
        is_playing = client.query("/live/clip/get/is_playing", (track_id, clip_id))[2]
        assert not bool(is_playing)

        # Scrub / stop scrub (no assertions, just ensure no errors)
        client.send_message("/live/clip/scrub", (track_id, clip_id, 0.25))
        client.send_message("/live/clip/stop/scrub", (track_id, clip_id))

        # Setup loop for duplicate_loop
        client.send_message("/live/clip/set/looping", (track_id, clip_id, 1))
        client.send_message("/live/clip/set/loop_start", (track_id, clip_id, 0.0))
        client.send_message("/live/clip/set/loop_end", (track_id, clip_id, 1.0))
        wait_one_tick()
        
        # Duplicate loop via both endpoints
        loop_end_before = client.query("/live/clip/get/loop_end", (track_id, clip_id))[2]
        client.send_message("/live/clip/duplicate_loop", (track_id, clip_id))
        wait_one_tick()
        loop_end_after = client.query("/live/clip/get/loop_end", (track_id, clip_id))[2]
        assert loop_end_after > loop_end_before

        client.send_message("/live/clip/duplicate/loop", (track_id, clip_id))
        wait_one_tick()
        loop_end_after2 = client.query("/live/clip/get/loop_end", (track_id, clip_id))[2]
        assert loop_end_after2 > loop_end_after

        # Fire button state
        client.send_message("/live/clip/set/fire_button", (track_id, clip_id, 1))
        client.send_message("/live/clip/set/fire_button", (track_id, clip_id, 0))

        # Quantize
        client.send_message("/live/clip/quantize", (track_id, clip_id, 4, 1.0))
        wait_one_tick()

        # Stop
        client.send_message("/live/clip/stop", (track_id, clip_id))
        wait_one_tick()
        is_playing = client.query("/live/clip/get/is_playing", (track_id, clip_id))[2]
        assert not bool(is_playing)

    finally:
        client.send_message("/live/song/stop_playing")
        client.send_message("/live/track/delete_clip", [track_id, clip_id])

# -----------------------------------------------------------------------------
# Test note functions on MIDI clips
# -----------------------------------------------------------------------------

def _parse_notes(rv):
    values = rv[2:]
    return [tuple(values[i:i + 5]) for i in range(0, len(values), 5)]

def _notes(client, track_id, clip_id):
    rv = client.query("/live/clip/get/notes", (track_id, clip_id))
    return _parse_notes(rv)

def _selected_notes(client, track_id, clip_id):
    rv = client.query("/live/clip/get/selected_notes", (track_id, clip_id))
    return _parse_notes(rv)

def _note_set(notes):
    return {(pitch, start_time) for pitch, start_time, _, _, _ in notes}

def _assert_notes_exact(notes, expected):
    assert _note_set(notes) == set(expected)
    
def _has_note(notes, pitch, start_time, tol=1e-6):
    return any(n_pitch == pitch and abs(n_start - start_time) < tol
                for n_pitch, n_start, _, _, _ in notes)

def _assert_notes_present(notes, expected):
    for pitch, start_time in expected:
        assert _has_note(notes, pitch, start_time), f"Missing note pitch={pitch} start={start_time}"


def test_clip_note_methods(client):
    """
    Test 1 (Add/Get/Replace/Remove/Listen)

    | P   | 0.0 | 0.5 | 1.0 |
    | --- | --- | --- | --- |
    | 27  |     |     | G   |
    | 26  |     | F   | C   |
    | 25  | E   | B   |     |
    | 24  | A   |     |     |
    """
    track_id = 0
    clip_id = 0

    client.send_message("/live/clip_slot/create_clip", [track_id, clip_id, 8.0])

    try:
        client.send_message("/live/clip/start_listen/notes", (track_id, clip_id))
        
        # Initial empty state
        rv = client.await_message("/live/clip/get/notes", timeout=TICK_DURATION * 2)
        _assert_notes_exact(_parse_notes(rv), [])

        # Add A,B,C
        client.send_message("/live/clip/add/notes", (track_id, clip_id,
                                                     24, 0.0, 0.5, 100, False,  # A
                                                     25, 0.5, 0.5, 100, False,  # B
                                                     26, 1.0, 0.5, 100, False)) # C
        rv = client.await_message("/live/clip/get/notes", timeout=TICK_DURATION * 2)
        _assert_notes_exact(_parse_notes(rv), [(24, 0.0), (25, 0.5), (26, 1.0)])

        # Range query: expect A,B (end exclusive)
        rv = client.query("/live/clip/get/notes", (track_id, clip_id, 24, 4, 0.0, 1.0))
        _assert_notes_exact(_parse_notes(rv), [(24, 0.0), (25, 0.5)])

        # Replace all with E,F,G
        client.send_message("/live/clip/replace/notes", (track_id, clip_id,
                                                         25, 0.0, 0.5, 100, False,  # E
                                                         26, 0.5, 0.5, 100, False,  # F
                                                         27, 1.0, 0.5, 100, False)) # G
        rv = client.await_message("/live/clip/get/notes", timeout=TICK_DURATION * 2)
        _assert_notes_exact(_parse_notes(rv), [(25, 0.0), (26, 0.5), (27, 1.0)])

        # Replace range (0.0..0.5) with A only -> A,F,G
        client.send_message("/live/clip/replace/notes", (track_id, clip_id,
                                                         24, 4, 0.0, 0.5,
                                                         24, 0.0, 0.5, 100, False))
        rv = client.await_message("/live/clip/get/notes", timeout=TICK_DURATION * 2)
        _assert_notes_exact(_parse_notes(rv), [(24, 0.0), (26, 0.5), (27, 1.0)])

        # Remove range (0.5..1.0) -> remove F, leaving A,G
        client.send_message("/live/clip/remove/notes", (track_id, clip_id, 24, 4, 0.5, 0.5))
        rv = client.await_message("/live/clip/get/notes", timeout=TICK_DURATION * 2)
        _assert_notes_exact(_parse_notes(rv), [(24, 0.0), (27, 1.0)])

        # Remove all
        client.send_message("/live/clip/remove/notes", (track_id, clip_id))
        rv = client.await_message("/live/clip/get/notes", timeout=TICK_DURATION * 2)
        _assert_notes_exact(_parse_notes(rv), [])
        
    finally: # Cleanup
        client.send_message("/live/clip/stop_listen/notes", (track_id, clip_id))
        client.send_message("/live/track/delete_clip", [track_id, clip_id])
    

def test_clip_note_selection(client):
    """
    Test 2 (Selection)

    | P   | 0.0 | 0.5 | 1.0 | 1.5 |
    | --- | --- | --- | --- | --- |
    | 27  |     |     |     | D   |
    | 26  |     | F   | C   |     |
    | 25  | E   | B   |     |     |
    | 24  | A   |     |     |     |
    """
    track_id = 0
    clip_id = 0

    client.send_message("/live/clip_slot/create_clip", [track_id, clip_id, 8.0])

    try:
        # Add A,B,C,D
        client.send_message("/live/clip/add/notes", (track_id, clip_id,
                                                    24, 0.0, 0.5, 100, False,  # A
                                                    25, 0.5, 0.5, 100, False,  # B
                                                    26, 1.0, 0.5, 100, False,  # C
                                                    27, 1.5, 0.5, 100, False)) # D
        wait_one_tick()
        _assert_notes_exact(_notes(client, track_id, clip_id), [(24, 0.0), (25, 0.5), (26, 1.0), (27, 1.5)])

        # Select A,B,C
        client.send_message("/live/clip/select/notes", (track_id, clip_id, 24, 4, 0.0, 1.5))
        wait_one_tick()
        _assert_notes_exact(_selected_notes(client, track_id, clip_id), [(24, 0.0), (25, 0.5), (26, 1.0)])

        # Deselect C (time_start=1.0, time_span=0.5)
        client.send_message("/live/clip/deselect/notes", (track_id, clip_id, 24, 4, 1.0, 0.5))
        wait_one_tick()
        _assert_notes_exact(_selected_notes(client, track_id, clip_id), [(24, 0.0), (25, 0.5)])

        # Replace selected with E,F (E=25@0.0, F=26@0.5)
        client.send_message("/live/clip/replace/selected_notes", (track_id, clip_id,
                                                                25, 0.0, 0.5, 100, False,  # E
                                                                26, 0.5, 0.5, 100, False)) # F
        wait_one_tick()
        _assert_notes_exact(_notes(client, track_id, clip_id), [(25, 0.0), (26, 0.5), (26, 1.0), (27, 1.5)])

        # Select E,F (time_start=0.0, time_span=1.0)
        client.send_message("/live/clip/select/notes", (track_id, clip_id, 24, 4, 0.0, 1.0))
        wait_one_tick()
        _assert_notes_exact(_selected_notes(client, track_id, clip_id), [(25, 0.0), (26, 0.5)])

        # Remove selected notes
        client.send_message("/live/clip/remove/selected_notes", (track_id, clip_id))
        wait_one_tick()
        _assert_notes_exact(_notes(client, track_id, clip_id), [(26, 1.0), (27, 1.5)])

        # Select all, then clear selection
        client.send_message("/live/clip/select/notes", (track_id, clip_id))
        wait_one_tick()
        _assert_notes_exact(_selected_notes(client, track_id, clip_id), [(26, 1.0), (27, 1.5)])
        client.send_message("/live/clip/deselect/notes", (track_id, clip_id))
        wait_one_tick()
        _assert_notes_exact(_selected_notes(client, track_id, clip_id), [])
    
    finally: # Cleanup
        client.send_message("/live/track/delete_clip", [track_id, clip_id])
    
    
def test_clip_note_duplication(client):
    """
    Test 3 (Duplication)
    
    | P   | 0.0 | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 | 3.0 | 3.5 | 4.0 | 4.5 | 5.0 | 5.5 | 6.0 | 6.5 | 7.0 | 7.5 | 8.0 | 8.5 | 9.0 |
    | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
    | 27  |     | 4   |     | 4   |     |     | 4   |     | 4   | 5   |     | 6   |     | 8   | 9   |     | 10  |     |     |
    | 26  | 4   |     | 4   |     |     | 4   |     | 4   |     |     |     |     |     |     |     |     |     |     | 11  |
    | 25  |     | 1   |     | 2   |     |     | 3   |     | 3   | 5   |     | 6   |     | 7   | 9   |     | 10  |     |     |
    | 24  | 1   |     | 2   |     |     | 3   |     | 3   |     |     |     |     |     |     |     |     |     |     | 11  |
    """
    track_id = 0
    clip_id = 0

    client.send_message("/live/clip_slot/create_clip", [track_id, clip_id, 10.0])

    try:
        # Test convert/note_number_to_name
        rv = client.query("/live/clip/convert/note_number_to_name", (track_id, clip_id, 60))
        assert isinstance(rv[2], str)
        assert rv[2] != ""

        # Step 1: add 2 notes (p24@0.0, p25@0.5), duration 0.5
        client.send_message("/live/clip/add/notes", (track_id, clip_id,
                                                    24, 0.0, 0.5, 100, False,
                                                    25, 0.5, 0.5, 100, False))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 2
        _assert_notes_present(notes, [(24, 0.0), (25, 0.5)])

        # Step 2: duplicate all notes (no args)
        client.send_message("/live/clip/duplicate/all_notes", (track_id, clip_id))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 4
        _assert_notes_present(notes, [(24, 1.0), (25, 1.5)])

        # Step 3: duplicate all notes to destination_time = 2.5
        client.send_message("/live/clip/duplicate/all_notes", (track_id, clip_id, 2.5, 0))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 8
        _assert_notes_present(notes, [(24, 2.5), (25, 3.0), (24, 3.5), (25, 4.0)])

        # Step 4: duplicate all notes to destination_time = 0, transposition = 2
        client.send_message("/live/clip/duplicate/all_notes", (track_id, clip_id, 0.0, 2))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 16
        _assert_notes_present(notes, [
            (26, 0.0), (27, 0.5), (26, 1.0), (27, 1.5),
            (26, 2.5), (27, 3.0), (26, 3.5), (27, 4.0),
        ])

        # Step 5: duplicate region (from_time=4.0, time_span=0.5)
        client.send_message("/live/clip/duplicate/region", (track_id, clip_id, 4.0, 0.5))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 18
        _assert_notes_present(notes, [(25, 4.5), (27, 4.5)])

        # Step 6: duplicate region (from_time=4.5, time_span=0.5, destination_time=5.5)
        client.send_message("/live/clip/duplicate/region", (track_id, clip_id, 4.5, 0.5, 5.5))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 20
        _assert_notes_present(notes, [(25, 5.5), (27, 5.5)])

        # Step 7: duplicate region (from_time=5.5, time_span=0.5, destination_time=6.5, pitch=25)
        client.send_message("/live/clip/duplicate/region", (track_id, clip_id, 5.5, 0.5, 6.5, 25))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 21
        _assert_notes_present(notes, [(25, 6.5)])

        # Step 8: duplicate region (from_time=5.5, time_span=0.5, destination_time=6.5, pitch=25, transposition=2)
        client.send_message("/live/clip/duplicate/region", (track_id, clip_id, 5.5, 0.5, 6.5, 25, 2))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 22
        _assert_notes_present(notes, [(27, 6.5)])

        # Step 9: select last two (time 6.5..7.0, pitches 24..27) then duplicate selected (no args)
        client.send_message("/live/clip/select/notes", (track_id, clip_id, 24, 4, 6.5, 0.5))
        wait_one_tick()
        client.send_message("/live/clip/duplicate/selected_notes", (track_id, clip_id))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 24
        _assert_notes_present(notes, [(25, 7.0), (27, 7.0)])

        # Step 10: select last two (time 7.0...7.5, pitches 24..27) then duplicate selected (destination_time = 8.0)
        client.send_message("/live/clip/select/notes", (track_id, clip_id, 24, 4, 7.0, 0.5))
        wait_one_tick()
        client.send_message("/live/clip/duplicate/selected_notes", (track_id, clip_id, 8.0))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 26
        _assert_notes_present(notes, [(25, 8.0), (27, 8.0)])

        # Step 11: select last two (time 8.0...8.5, pitches 24..27) then duplicate selected (destination_time = 9.0, transposition = -1)
        client.send_message("/live/clip/select/notes", (track_id, clip_id, 24, 4, 8.0, 0.5))
        wait_one_tick()
        client.send_message("/live/clip/duplicate/selected_notes", (track_id, clip_id, 9.0, -1))
        wait_one_tick()
        notes = _notes(client, track_id, clip_id)
        assert len(notes) == 28
        _assert_notes_present(notes, [(24, 9.0), (26, 9.0)])
    
    finally: # Cleanup
        client.send_message("/live/track/delete_clip", [track_id, clip_id])


# By-ID flows - Not to be implemented yet.
# /live/clip/get/notes_by_id          (ids list)
# /live/clip/replace/notes_by_id      (ids list + 5-field list)
# /live/clip/select/notes_by_id       (ids list)
# /live/clip/deselect/notes_by_id     (ids list)
# /live/clip/remove/notes_by_id       (ids list)
# /live/clip/modify/notes             (9-field per note: includes note_id)
# _delete_midi_clip


# -----------------------------------------------------------------------------
# Test warp and time conversion functions on audio clips
# -----------------------------------------------------------------------------

def test_clip_warp_markers(client, silent_audio_file):
    """
    Use the listener to confirm edits
    Warp markers snap to samples, allow some small amount of variation (1E-4) for matching"""
    track_id = 2
    clip_id = 0
    tol = 1e-4

    def _parse_markers(rv):
        values = rv[2:]
        return [(values[i], values[i + 1]) for i in range(0, len(values), 2)]

    def _assert_markers_exact(markers, expected):
        assert len(markers) == len(expected)
        for (beat, sample), (exp_beat, exp_sample) in zip(markers, expected):
            assert abs(beat - exp_beat) < tol
            assert abs(sample - exp_sample) < tol

    client.send_message("/live/clip_slot/create/audio_clip", (2, 0, str(silent_audio_file)))
    
    try:
        client.send_message("/live/clip/start_listen/warp_markers", (track_id, clip_id))

        # Initial markers
        rv = client.query("/live/clip/get/warp_markers", (track_id, clip_id))
        markers = _parse_markers(rv)
        _assert_markers_exact(markers, [(0.0, 0.0), (16.0, 8.0)])        

        # Add marker at beat 8, sample 4
        client.send_message("/live/clip/add/warp_marker", (track_id, clip_id, 8.0, 4.0))
        rv = client.await_message("/live/clip/get/warp_markers", timeout=TICK_DURATION * 2)
        markers = _parse_markers(rv)
        _assert_markers_exact(markers, [(0.0, 0.0), (8.0, 4.0), (16.0, 8.0)])

        # Add marker at beat 12 (sample inferred)
        client.send_message("/live/clip/add/warp_marker", (track_id, clip_id, 12.0))
        rv = client.await_message("/live/clip/get/warp_markers", timeout=TICK_DURATION * 2)
        markers = _parse_markers(rv)
        _assert_markers_exact(markers, [(0.0, 0.0), (8.0, 4.0), (12.0, 6.0), (16.0, 8.0)])

        # Remove marker at beat 0
        client.send_message("/live/clip/remove/warp_marker", (track_id, clip_id, 0.0))
        rv = client.await_message("/live/clip/get/warp_markers", timeout=TICK_DURATION * 2)
        markers = _parse_markers(rv)
        _assert_markers_exact(markers, [(8.0, 4.0), (12.0, 6.0), (16.0, 8.0)])

        # Move marker at beat 8 by -4 beats
        client.send_message("/live/clip/move/warp_marker", (track_id, clip_id, 8.0, -4.0))
        rv = client.await_message("/live/clip/get/warp_markers", timeout=TICK_DURATION * 2)
        markers = _parse_markers(rv)
        _assert_markers_exact(markers, [(4.0, 4.0), (12.0, 6.0), (16.0, 8.0)])

        client.send_message("/live/clip/stop_listen/warp_markers", (track_id, clip_id))
        
    finally:
        client.send_message("/live/clip_slot/delete/clip", (2, 0))
        wait_one_tick()

def test_clip_convert_time(client, silent_audio_file):
    track_id = 2
    clip_id = 0
    tol = 1e-4

    def _assert_close(actual, expected):
        assert abs(actual - expected) < tol

    client.send_message("/live/clip_slot/create/audio_clip", (track_id, clip_id, str(silent_audio_file)))

    try:
        sample_rate = client.query("/live/clip/get/sample_rate", (track_id, clip_id))[2]
        beats_val = 2.0
        seconds_val = 1.0  # 2 beats @ 120 bpm
        samples_val = sample_rate * seconds_val

        # beats -> seconds
        rv = client.query("/live/clip/convert/time", (track_id, clip_id, "beats", "seconds", beats_val))
        _assert_close(rv[2], seconds_val)

        # beats -> samples
        rv = client.query("/live/clip/convert/time", (track_id, clip_id, "beats", "samples", beats_val))
        _assert_close(rv[2], samples_val)

        # seconds -> beats
        rv = client.query("/live/clip/convert/time", (track_id, clip_id, "seconds", "beats", seconds_val))
        _assert_close(rv[2], beats_val)

        # seconds -> samples
        rv = client.query("/live/clip/convert/time", (track_id, clip_id, "seconds", "samples", seconds_val))
        _assert_close(rv[2], samples_val)

        # samples -> seconds
        rv = client.query("/live/clip/convert/time", (track_id, clip_id, "samples", "seconds", samples_val))
        _assert_close(rv[2], seconds_val)

        # samples -> beats
        rv = client.query("/live/clip/convert/time", (track_id, clip_id, "samples", "beats", samples_val))
        _assert_close(rv[2], beats_val)

    finally:
        client.send_message("/live/clip_slot/delete/clip", (track_id, clip_id))
        wait_one_tick()



# -----------------------------------------------------------------------------
# Test Clip Properties
# -----------------------------------------------------------------------------

def test_clip_properties_midi(client):
    track_id = 0
    clip_id = 0
    
    properties_midi = {           # (get, set, listen, set_value)
        "automation_envelopes":     (0, 0, 0, None),
        "canonical_parent":         (0, 0, 0, None),
        "color":                    (1, 1, 1, 1716118),
        "color_index":              (1, 1, 1, 40),
        "end_marker":               (1, 1, 1, 6),
        "start_marker":             (1, 1, 1, 2),
        "start_time":               (1, 0, 1, None),
        "end_time":                 (1, 0, 1, None),
        "groove":                   (0, 0, 0, None),
        "has_envelopes":            (1, 0, 1, None),
        "has_groove":               (1, 0, 0, None),
        "is_arrangement_clip":      (1, 0, 0, None),
        "is_midi_clip":             (1, 0, 0, None),
        "is_audio_clip":            (1, 0, 0, None),
        "is_overdubbing":           (1, 0, 1, None),
        "is_playing":               (1, 1, 0, 1),
        "is_recording":             (1, 0, 1, 0),
        "is_session_clip":          (1, 0, 0, 0),
        "is_take_lane_clip":        (1, 0, 0, 0),
        "is_triggered":             (1, 0, 0, 0),
        "launch_mode":              (1, 1, 1, 1),
        "launch_quantization":      (1, 1, 1, 1),
        "legato":                   (1, 1, 1, 1),
        "length":                   (1, 0, 0, None),
        "loop_end":                 (1, 1, 1, 6),
        "loop_jump":                (0, 0, 0, None), # listener is bang, test elsewhere
        "loop_start":               (1, 1, 1, 2),
        "looping":                  (1, 1, 1, 0),
        "muted":                    (1, 1, 1, 1),
        "name":                     (1, 1, 1, "new_name"),
        "playing_position":         (1, 0, 1, None),
        "playing_status":           (0, 0, 0, None), # listener is bang, test elsewhere
        "position":                 (1, 1, 1, 0),
        "signature_denominator":    (1, 1, 1, 8),
        "signature_numerator":      (1, 1, 1, 6),
        "velocity_amount":          (1, 1, 1, 1),
        "will_record_on_start":     (1, 0, 0, None),
    }
    
    client.send_message("/live/clip_slot/create/midi_clip", (track_id, clip_id, 8))
    client.send_message("/live/song/set/clip_trigger_quantization", (0))
    
    try:
        for prop, spec in properties_midi.items():
            # Read/Write Properties
            if spec[0] and spec[1]:
                client.send_message(f"/live/clip/get/{prop}", (track_id, clip_id))
                client.send_message(f"/live/clip/set/{prop}", (track_id, clip_id, spec[3]))
                wait_one_tick()
                assert client.query(f"/live/clip/get/{prop}", (track_id, clip_id)) == (track_id, clip_id, spec[3])
            
            # Read Only Properties
            if spec[0] and not spec[1]:
                assert client.query(f"/live/clip/get/{prop}", (track_id, clip_id))[:2] == (track_id, clip_id)
                
            # Listeners
            if spec[2]:
                client.send_message(f"/live/clip/start_listen/{prop}", (track_id, clip_id))
                assert client.await_message(f"/live/clip/get/{prop}", TICK_DURATION * 2)[:2] == (track_id, clip_id)
                client.send_message(f"/live/clip/stop_listen/{prop}", (track_id, clip_id))

    finally:
        client.send_message("/live/song/stop_playing")
        client.send_message("/live/clip_slot/delete/clip", (track_id, clip_id))
        wait_one_tick()

def test_bang_listeners(client):
    track_id = 0
    clip_id = 0
    
    client.send_message("/live/clip_slot/create/midi_clip", (track_id, clip_id, 8))
    client.send_message("/live/song/set/clip_trigger_quantization", (0))
    
    try:
        # Playing status
        client.send_message("/live/clip/set/end_marker", (track_id, clip_id, .5))
        client.send_message("/live/clip/set/looping", (track_id, clip_id, 0))
        wait_one_tick()
        
        client.send_message("/live/clip/start_listen/playing_status", (track_id, clip_id))
        client.send_message("/live/clip/fire", (track_id, clip_id))
        assert client.await_message("/live/clip/get/playing_status", TICK_DURATION * 2) == (track_id, clip_id, 1)
        client.send_message("/live/clip/stop_listen/playing_status", (track_id, clip_id))
        
        # Loop Jump
        client.send_message("/live/clip/set/looping", (track_id, clip_id, 1))
        client.send_message("/live/clip/set/loop_end", (track_id, clip_id, .25))
        wait_one_tick()
        
        client.send_message("/live/clip/fire", (track_id, clip_id))
        client.send_message("/live/clip/start_listen/loop_jump", (track_id, clip_id))
        assert client.await_message("/live/clip/get/loop_jump", TICK_DURATION * 20) == (track_id, clip_id, 1)
        client.send_message("/live/clip/stop_listen/loop_jump", (track_id, clip_id))
        
    finally:
        client.send_message("/live/song/stop_playing")
        client.send_message("/live/clip_slot/delete/clip", (track_id, clip_id))
        wait_one_tick()


# -----------------------------------------------------------------------------
# test_clip_audio_properties (Audio)
# -----------------------------------------------------------------------------
def test_clip_properties_audio(client, silent_audio_file):
    track_id = 2
    clip_id = 0
    properties_audio = {      # (get, set, listen, set_value)
        "available_warp_modes": (1, 0, 0, None),
        "file_path":            (1, 0, 1, None),
        "gain":                 (1, 1, 1, 1),
        "gain_display_string":  (1, 0, 0, None),
        "pitch_coarse":         (1, 1, 1, 1),
        "pitch_fine":           (1, 1, 1, 1),
        "ram_mode":             (1, 1, 1, 0),
        "sample_length":        (1, 0, 0, None),
        "sample_rate":          (1, 0, 0, None),
        "warp_mode":            (1, 1, 1, 1),
        "warp_markers":         (1, 0, 1, None),
        "warping":              (1, 1, 1, 0),
    }
    
    client.send_message("/live/clip_slot/create/audio_clip", (track_id, clip_id, str(silent_audio_file)))
    client.send_message("/live/song/set/clip_trigger_quantization", (0))
    
    try:
        for prop, spec in properties_audio.items():
            # Read/Write Properties
            if spec[0] and spec[1]:
                client.send_message(f"/live/clip/get/{prop}", (track_id, clip_id))
                client.send_message(f"/live/clip/set/{prop}", (track_id, clip_id, spec[3]))
                wait_one_tick()
                assert client.query(f"/live/clip/get/{prop}", (track_id, clip_id)) == (track_id, clip_id, spec[3])
            
            # Read Only Properties
            if spec[0] and not spec[1]:
                assert client.query(f"/live/clip/get/{prop}", (track_id, clip_id))[:2] == (track_id, clip_id)
                
            # Listeners
            if spec[2]:
                client.send_message(f"/live/clip/start_listen/{prop}", (track_id, clip_id))
                assert client.await_message(f"/live/clip/get/{prop}", TICK_DURATION * 2)[:2] == (track_id, clip_id)
                client.send_message(f"/live/clip/stop_listen/{prop}", (track_id, clip_id))

    finally:
        client.send_message("/live/clip_slot/delete/clip", (track_id, clip_id))
        wait_one_tick()


# -----------------------------------------------------------------------------
# Test Clip View
# -----------------------------------------------------------------------------

def test_clip_view_commands(client):
    track_id = 0
    clip_id = 0

    client.send_message("/live/clip_slot/create_clip", [track_id, clip_id, 8.0])

    try:
        # Basic view actions (no observable state to assert)
        client.send_message("/live/clip/view/show/loop", (track_id, clip_id))
        client.send_message("/live/clip/view/show/envelope", (track_id, clip_id))
        client.send_message("/live/clip/view/hide/envelope", (track_id, clip_id))

        # Grid triplet
        client.send_message("/live/clip/view/set/grid_is_triplet", (track_id, clip_id, 1))
        wait_one_tick()
        assert client.query("/live/clip/view/get/grid_is_triplet", (track_id, clip_id)) == (track_id, clip_id, 1)

        # Grid quantization
        client.send_message("/live/clip/view/set/grid_quantization", (track_id, clip_id, 7))
        wait_one_tick()
        assert client.query("/live/clip/view/get/grid_quantization", (track_id, clip_id)) == (track_id, clip_id, 7)

    finally:
        client.send_message("/live/track/delete_clip", [track_id, clip_id])
