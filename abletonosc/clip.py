import re
from typing import Tuple, Any
from .handler import AbletonOSCHandler
import Live

def note_name_to_midi(name):
    """ Maps a MIDI note name (D3, C#6) to a value.
    Assumes that middle C is C4. """
    note_names = [["C"],
                  ["C#", "Db"],
                  ["D"],
                  ["D#", "Eb"],
                  ["E"],
                  ["F"],
                  ["F#", "Gb"],
                  ["G"],
                  ["G#", "Ab"],
                  ["A"],
                  ["A#", "Bb"],
                  ["B"]]

    for index, names in enumerate(note_names):
        if name in names:
            return index
    return None

def _chunk(params: Tuple[Any], size: int):
    if len(params) % size != 0:
        raise ValueError("Invalid number of arguments. Expected input to split into %d-size chunks." % size)
    return (params[i:i + size] for i in range(0, len(params), size))

class ClipHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "clip"
        self._clip_notes_cache = []

    def init_api(self):
        def create_clip_callback(func, *args, pass_clip_index=False, **kwargs):
            """
            Creates a callback that expects the following set of arguments:
              (track_index, clip_index, *args)

            The callback then extracts the relevant `Clip` object from the current Song,
            and calls `func` with this `Clip` object plus any additional *args.

            pass_clip_index is a bit of an ugly hack, although seems like the lesser of
            evils for scenarios where the track/clip index is needed (as a clip is unable
            to query its own index). Other alternatives include _always_ passing track/clip
            index to the callback, but this adds arg clutter to every single callback.
            """

            def clip_callback(params: Tuple[Any]) -> Tuple:
                #--------------------------------------------------------------------------------
                # Cast to int to support clients such as TouchOSC that, by default, pass all
                # numeric arguments as float.
                #--------------------------------------------------------------------------------
                track_index, clip_index = int(params[0]), int(params[1])
                track = self.song.tracks[track_index]
                clip = track.clip_slots[clip_index].clip
                if pass_clip_index:
                    rv = func(clip, *args, tuple(params[0:]), **kwargs)
                else:
                    rv = func(clip, *args, tuple(params[2:]), **kwargs)

                if rv is not None:
                    return (track_index, clip_index, *rv)

            return clip_callback

        def create_arrangement_clip_callback(func, *args, pass_clip_index=False, **kwargs):
            """
            Creates a callback that expects: (track_index, arrangement_clip_index, *args)
            and targets track.arrangement_clips[clip_index].
            """
            def clip_callback(params: Tuple[Any]) -> Tuple:
                track_index, clip_index = int(params[0]), int(params[1])
                track = self.song.tracks[track_index]
                clip = track.arrangement_clips[clip_index]
                if pass_clip_index:
                    rv = func(clip, *args, tuple(params[0:]), **kwargs)
                else:
                    rv = func(clip, *args, tuple(params[2:]), **kwargs)

                if rv is not None:
                    return (track_index, clip_index, *rv)

            return clip_callback
        
        
        # --- Method / Property Definitions --- #
        methods = {
            # Playback / Transport
            "fire":             {"alias": 0, "caller": 1},
            "stop":             {"alias": 0, "caller": 1},
            "set/fire_button":  {"alias": 1, "caller": "set_fire_button_state"},
            "scrub":            {"alias": 0, "caller": 1},
            "stop/scrub":       {"alias": 1, "caller": "stop_scrub"},
            "move/playing_pos": {"alias": 1, "caller": "move_playing_pos"},
            "crop":             {"alias": 0, "caller": 1},
            "duplicate_loop":   {"alias": 0, "caller": 1},                       # Already in master, kept for back-compat
            "duplicate/loop":   {"alias": 1, "caller": "duplicate_loop"},
            "quantize":         {"alias": 0, "caller": 1},
            "quantize/pitch":   {"alias": 1, "caller": "quantize_pitch"},

            # Warp / Time Conversions
            "add/warp_marker":      {"alias": 0, "caller": "clip_add_warp_marker"},
            "move/warp_marker":     {"alias": 1, "caller": "move_warp_marker"},
            "remove/warp_marker":   {"alias": 1, "caller": "remove_warp_marker"},
            "convert/time":         {"alias": 0, "caller": "clip_convert_time"},

            # Notes
            "add/notes":                    {"alias": 0, "caller": "clip_add_notes"},
            "get/notes":                    {"alias": 0, "caller": "clip_get_notes"}, # Warns
            "get/selected_notes":           {"alias": 0, "caller": "clip_get_selected_notes"}, # Warns
            "replace/notes":                {"alias": 0, "caller": "clip_replace_notes"}, # Warns
            "replace/selected_notes":       {"alias": 0, "caller": "clip_replace_selected_notes"}, # Warns
            "remove/notes":                 {"alias": 0, "caller": "clip_remove_notes"},
            "remove/selected_notes":        {"alias": 0, "caller": "clip_remove_selected_notes"},
            "duplicate/all_notes":          {"alias": 0, "caller": "clip_duplicate_all_notes"},
            "duplicate/region":             {"alias": 0, "caller": "clip_duplicate_region"},
            "duplicate/selected_notes":     {"alias": 0, "caller": "clip_duplicate_selected_notes"},
            "select/notes":                 {"alias": 0, "caller": "clip_select_notes"},
            "deselect/notes":               {"alias": 0, "caller": "clip_deselect_notes"},
            "convert/note_number_to_name":  {"alias": 0, "caller": "clip_note_number_to_name"},
            
            # # By ID, TODO: Need to decide on how to implement extended note format while keeping back-compat.
            # "modify/notes":                 {"alias": 0, "caller": "clip_apply_note_modifications"},
            # "get/notes_by_id":              {"alias": 0, "caller": "clip_get_notes_by_id"},
            # "replace/notes_by_id":          {"alias": 0, "caller": "clip_replace_notes_by_id"},
            # "remove_notes_by_id":           {"alias": 0, "caller": None}, # Remove undocumented/unusable back-compat
            # "remove/notes_by_id":           {"alias": 1, "caller": "remove_notes_by_id"},
            # "duplicate/notes_by_id":        {"alias": 0, "caller": None},                               # TODO: Decide on format since arg length is variable with optional time/transpose
            # "select/notes_by_id":           {"alias": 1, "caller": "select_notes_by_id"},
            # "deselect/notes_by_id":         {"alias": 0, "caller": "clip_deselect_notes_by_id"},

            # Automation / envelopes
            # TODO: Envelope objects
            "automation/envelope":          {"alias": 0, "caller": None},
            "create/automation_envelope":   {"alias": 0, "caller": None},
            "clear/envelope":               {"alias": 0, "caller": None},
            "clear/all_envelopes":          {"alias": 0, "caller": None},
        }
        
        properties = {
            "automation_envelopes":     {"get": 0, "set": 0, "listen": 0},  # TODO: Const access to a list of all automation envelopes for this clip.
            "available_warp_modes":     {"get": "clip_get_available_warp_modes", "set": 0, "listen": 0},
            "canonical_parent":         {"get": 0, "set": 0, "listen": 0},  # TODO: ClipSlot object: Not serializable
            "color":                    {"get": 1, "set": 1, "listen": 1},
            "color_index":              {"get": 1, "set": 1, "listen": 1},
            "end_marker":               {"get": 1, "set": 1, "listen": 1},
            "end_time":                 {"get": 1, "set": 0, "listen": 1},
            "file_path":                {"get": 1, "set": 0, "listen": 1},  # Listener triggers with replace file actions.
            "gain":                     {"get": 1, "set": 1, "listen": 1},
            "gain_display_string":      {"get": 1, "set": 0, "listen": 0},
            "groove":                   {"get": 0, "set": 0, "listen": 0},  # TODO: Groove object; Need groove module
            "has_envelopes":            {"get": 1, "set": 0, "listen": 1},
            "has_groove":               {"get": 1, "set": 0, "listen": 0},
            "is_arrangement_clip":      {"get": 1, "set": 0, "listen": 0},
            "is_midi_clip":             {"get": 1, "set": 0, "listen": 0},
            "is_audio_clip":            {"get": 1, "set": 0, "listen": 0},
            "is_overdubbing":           {"get": 1, "set": 0, "listen": 1},
            "is_playing":               {"get": 1, "set": 1, "listen": 0},
            "is_recording":             {"get": 1, "set": 0, "listen": 1},
            "is_session_clip":          {"get": 1, "set": 0, "listen": 0},
            "is_take_lane_clip":        {"get": 1, "set": 0, "listen": 0},
            "is_triggered":             {"get": 1, "set": 0, "listen": 0},
            "launch_mode":              {"get": 1, "set": 1, "listen": 1},
            "launch_quantization":      {"get": 1, "set": 1, "listen": 1},
            "legato":                   {"get": 1, "set": 1, "listen": 1},
            "length":                   {"get": 1, "set": 0, "listen": 0},
            "loop_end":                 {"get": 1, "set": 1, "listen": 1},
            "loop_jump":                {"get": 0, "set": 0, "listen": "bang"},  # Sends bang (1) when the loop crosses the start marker.
            "loop_start":               {"get": 1, "set": 1, "listen": 1},
            "looping":                  {"get": 1, "set": 1, "listen": 1},
            "muted":                    {"get": 1, "set": 1, "listen": 1},
            "name":                     {"get": 1, "set": 1, "listen": 1},
            "notes":                    {"get": 0, "set": 0, "listen": "clip_get_notes_listener"},
            "pitch_coarse":             {"get": 1, "set": 1, "listen": 1},
            "pitch_fine":               {"get": 1, "set": 1, "listen": 1},
            "playing_position":         {"get": 1, "set": 0, "listen": 1},
            "playing_status":           {"get": 0, "set": 0, "listen": "bang"},  # bangs when playing/trigger state changes. Check is_playing/is_triggerd for details
            "position":                 {"get": 1, "set": 1, "listen": 1},
            "ram_mode":                 {"get": 1, "set": 1, "listen": 1},
            "sample_length":            {"get": 1, "set": 0, "listen": 0},
            "sample_rate":              {"get": 1, "set": 0, "listen": 0},
            "signature_denominator":    {"get": 1, "set": 1, "listen": 1},
            "signature_numerator":      {"get": 1, "set": 1, "listen": 1},
            "start_marker":             {"get": 1, "set": 1, "listen": 1},
            "start_time":               {"get": 1, "set": 0, "listen": 1},
            "velocity_amount":          {"get": 1, "set": 1, "listen": 1},
            "warp_mode":                {"get": 1, "set": 1, "listen": 1},
            "warp_markers":             {"get": "clip_get_warp_markers", "set": 0, "listen": "clip_get_warp_markers_listener"},
            "warping":                  {"get": 1, "set": 1, "listen": 1},
            "will_record_on_start":     {"get": 1, "set": 0, "listen": 0},
        }
            
        # --- Custom Callers --- #
        
        # Warping / Time
        def clip_get_available_warp_modes(clip, _):
            value = tuple(int(mode) for mode in clip.available_warp_modes)
            self.logger.info("Getting property for %s: available_warp_modes = %s" % (self.class_identifier, value))
            return value
        
        def clip_get_warp_markers(clip, _, log: bool = True):
            markers = clip.warp_markers
            # Drop trailing shadow marker (used internally to determine final segment BPM).
            if markers:
                markers = markers[:-1]
            flat: list[float] = []
            for marker in markers:
                flat.append(getattr(marker, "beat_time", None))
                flat.append(getattr(marker, "sample_time", None))
            value = tuple(flat)
            if log:
                self.logger.info("Getting property for %s: warp_markers = %s" % (self.class_identifier, value))
            return value

        def clip_get_warp_markers_listener(clip, params: Tuple[Any] = ()):
            return clip_get_warp_markers(clip, (), log=False)
        
        def clip_add_warp_marker(clip, params: Tuple[Any] = ()):
            self.logger.info("Calling method for %s: add_warp_marker (params %s)" % (self.class_identifier, params))
            if len(params) == 1:
                beat_time = params[0]
                sample_time = None
            elif len(params) == 2:
                beat_time, sample_time = params
            else:
                raise ValueError("Invalid number of arguments for /clip/add_warp_marker. Pass beat_time or beat_time, sample_time.")

            if sample_time is None:
                sample_rate = clip.sample_rate
                samples = clip.beat_to_sample_time(beat_time)
                sample_time = samples / sample_rate

            warp_marker = Live.Clip.WarpMarker(sample_time, beat_time)
            clip.add_warp_marker(warp_marker)
            
        def clip_convert_time(clip, params: Tuple[Any] = ()):
            if len(params) != 3:
                raise ValueError("Invalid number of arguments for /clip/convert/time. Expected (unit_from, unit_to, value).")
            unit_from, unit_to, input = params
            units = ("samples", "seconds", "beats")
            if unit_from not in units or unit_to not in units:
                raise ValueError("Invalid units for /clip/convert/time. Use 'samples', 'seconds', or 'beats'.")
            if unit_from == unit_to:
                value = (input,)
                self.logger.info("Time conversion for %s: %s %s -> %s %s" % (
                    self.class_identifier, input, unit_from, input, unit_to))
                return value

            sample_rate = clip.sample_rate

            # Beat-based conversions require a warped clip; seconds<->samples always works.
            if unit_from == "beats":
                samples = clip.beat_to_sample_time(input)
            elif unit_from == "seconds":
                samples = input * sample_rate
            else:  # already samples
                samples = input

            if unit_to == "beats":
                value = clip.sample_to_beat_time(samples)
            elif unit_to == "seconds":
                value = samples / sample_rate
            else:
                value = samples
            self.logger.info("Time conversion for %s: %s %s -> %s %s" % (
                self.class_identifier, input, unit_from, value, unit_to))
            return (value,)

        # Notes
        def clip_note_number_to_name(clip, params: Tuple[Any] = ()):
            if len(params) < 1:
                raise ValueError("Invalid number of arguments for /clip/convert/note_number_to_name. Expected 1 argument.")
            value = clip.note_number_to_name(params[0])
            self.logger.info("Converting note for %s: %s -> %s" % (self.class_identifier, params[0], value))
            return (value,)
        
        def clip_add_notes(clip, params: Tuple[Any] = ()):
            if len(params) % 5 != 0:
                raise ValueError("Invalid number of arguments for /clip/add/notes. Expected list of 5 parameters per note.")
            self.logger.info("Calling method for %s: add_notes (params %s)" % (self.class_identifier, params))
            notes = []
            for pitch, start_time, duration, velocity, mute in _chunk(params, 5):
                note = Live.Clip.MidiNoteSpecification(start_time=start_time,
                                                       duration=duration,
                                                       pitch=pitch,
                                                       velocity=velocity,
                                                       mute=mute)
                notes.append(note)
            clip.add_new_notes(tuple(notes))
        
        def _notes_have_extended_attrs(notes):
            for note in notes:
                if (note.probability != 1.0 or
                        note.velocity_deviation != 0.0 or
                        note.release_velocity != 64):
                    return True
            return False

        def _clip_serialize_notes(notes, include_extended: bool):
            all_note_attributes = []
            if not include_extended and _notes_have_extended_attrs(notes):
                self.logger.warning(
                    "Notes in clip %s have extended attributes that were not returned." % (self.class_identifier)
                )
            for note in notes:
                all_note_attributes += [note.pitch, note.start_time, note.duration, note.velocity, note.mute]
                if include_extended:
                    all_note_attributes += [
                        note.note_id,
                        note.probability,
                        note.velocity_deviation,
                        note.release_velocity,
                    ]
            return tuple(all_note_attributes)

        def clip_get_notes(clip, params: Tuple[Any], include_extended: bool = False, log: bool = True):
            if len(params) == 4:
                pitch_start, pitch_span, time_start, time_span = params
            elif len(params) == 0:
                pitch_start, pitch_span, time_start, time_span = 0, 127, -8192, 16384
            else:
                raise ValueError("Invalid number of arguments for /clip/get/notes. Either 0 or 4 arguments must be passed.")
            notes = clip.get_notes_extended(pitch_start, pitch_span, time_start, time_span)
            value = _clip_serialize_notes(notes, include_extended)
            if log:
                self.logger.info("Getting property for %s: notes%s = %s" % (self.class_identifier, "_extended" if include_extended else "", value))
            return value

        def clip_get_notes_listener(clip, params: Tuple[Any] = ()):
            return clip_get_notes(clip, (), include_extended=False, log=False)

        def clip_get_selected_notes(clip, params: Tuple[Any] = (), include_extended: bool = False):
            notes = clip.get_selected_notes_extended()
            value = _clip_serialize_notes(notes, include_extended)
            self.logger.info("Getting property for %s: selected_notes = %s" % (self.class_identifier, value))
            return value
        
        def clip_replace_notes(clip, params: Tuple[Any]):
            if len(params) % 5 == 4:
                pitch_start, pitch_span, time_start, time_span = params[:4]
                note_params = params[4:]
            elif len(params) % 5 == 0:
                pitch_start, pitch_span, time_start, time_span = 0, 127, -8192, 16384
                note_params = params
            else:
                raise ValueError("Invalid number of arguments for /clip/replace/notes. Either 0 or 4 arguments plus a list of notes must be passed.")
            self.logger.info("Calling method for %s: replace_notes (params %s)" % (self.class_identifier, params))
            old_notes = clip.get_notes_extended(pitch_start, pitch_span, time_start, time_span)
            if _notes_have_extended_attrs(old_notes):
                self.logger.warning("Notes in clip %s have extended attributes that were not returned." % (self.class_identifier))
            clip.remove_notes_extended(pitch_start, pitch_span, time_start, time_span)
            notes = []
            for pitch, start_time, duration, velocity, mute in _chunk(note_params, 5):
                note = Live.Clip.MidiNoteSpecification(start_time=start_time,
                                                       duration=duration,
                                                       pitch=pitch,
                                                       velocity=velocity,
                                                       mute=mute)
                notes.append(note)
            clip.add_new_notes(tuple(notes))
        
        def clip_replace_selected_notes(clip, params: Tuple[Any] = ()):
            if len(params) % 5 != 0:
                raise ValueError("Invalid number of arguments for /clip/replace/selected_notes. Expected list of 5 parameters per note.")
            self.logger.info("Calling method for %s: replace_selected_notes (params %s)" % (self.class_identifier, params))
            old_notes = clip.get_selected_notes_extended()
            if _notes_have_extended_attrs(old_notes):
                self.logger.warning("Selected notes in clip %s have extended attributes that were not returned." % (self.class_identifier))
            old_ids = [n.note_id for n in old_notes]
            if len(old_ids) == 0:
                raise ValueError("No notes are selected for replacement.")
            clip.remove_notes_by_id(old_ids)
            notes = []
            for pitch, start_time, duration, velocity, mute in _chunk(params, 5):
                note = Live.Clip.MidiNoteSpecification(start_time=start_time,
                                                       duration=duration,
                                                       pitch=pitch,
                                                       velocity=velocity,
                                                       mute=mute)
                notes.append(note)
            clip.add_new_notes(tuple(notes))
        
        def clip_remove_notes(clip, params: Tuple[Any] = ()):
            self.logger.info("Calling method for %s: remove_notes (params %s)" % (self.class_identifier, params))
            if len(params) == 4:
                pitch_start, pitch_span, time_start, time_span = params
            elif len(params) == 0:
                pitch_start, pitch_span, time_start, time_span = 0, 127, -8192, 16384
            else:
                raise ValueError("Invalid number of arguments for /clip/remove/notes. Either 0 or 4 arguments must be passed.")
            clip.remove_notes_extended(pitch_start, pitch_span, time_start, time_span)
            
        def clip_remove_selected_notes(clip, params: Tuple[Any] = ()):
            self.logger.info("Calling method for %s: remove_selected_notes (params %s)" % (self.class_identifier, params))
            old_notes = clip.get_selected_notes_extended()
            if _notes_have_extended_attrs(old_notes):
                self.logger.warning("Selected notes in clip %s have extended attributes that were not returned." % (self.class_identifier))
            old_ids = [n.note_id for n in old_notes]
            if len(old_ids) == 0:
                raise ValueError("No notes are selected for removal.")
            clip.remove_notes_by_id(old_ids)
        
        def clip_duplicate_all_notes(clip, params: Tuple[Any] = ()):
            destination_time = -1
            transposition = 0
            if len(params) == 2:
                destination_time, transposition = params
            elif len(params) == 1:
                destination_time = params[0]
            elif len(params) > 2:
                raise ValueError("Invalid number of arguments for /clip/duplicate/all_notes. 1-2 arguments must be passed.")
            self.logger.info("Calling method for %s: duplicate_all_notes (params %s)" % (self.class_identifier, params))
            notes = clip.get_all_notes_extended()
            if len(notes) == 0:
                raise ValueError("Clip has no notes to duplicate.")
            from_time = min([n.start_time for n in notes])
            end_time = max([n.start_time + n.duration for n in notes])
            time_span = end_time - from_time
            if destination_time == -1:
                destination_time = end_time
            clip.duplicate_region(from_time, time_span, destination_time, -1, transposition)
        
        def clip_duplicate_region(clip, params: Tuple[Any] = ()):
            self.logger.info("Calling method for %s: duplicate_region (params %s)" % (self.class_identifier, params))
            transposition = 0
            pitch = -1
            destination_time = -1
            if len(params) == 5:
                from_time, time_span, destination_time, pitch, transposition = params
            elif len(params) == 4:
                from_time, time_span, destination_time, pitch = params
            elif len(params) == 3:
                from_time, time_span, destination_time = params
            elif len(params) == 2:
                from_time, time_span = params
            else:
                raise ValueError("Invalid number of arguments for /clip/duplicate/region. 2, 3, 4, or 5 arguments must be passed.")
            if destination_time == -1:
                destination_time = from_time + time_span
            clip.duplicate_region(from_time, time_span, destination_time, pitch, transposition)

        def clip_duplicate_selected_notes(clip, params: Tuple[Any] = ()):
            if len(params) > 2:
                raise ValueError("Invalid number of arguments for /clip/duplicate/selected_notes. 0-2 arguments must be passed.")
            self.logger.info("Calling method for %s: duplicate_selected_notes (params %s)" % (self.class_identifier, params))
            notes = clip.get_selected_notes_extended()
            if len(notes) == 0:
                raise ValueError("No notes are selected for duplication.")
            note_ids = [n.note_id for n in notes]
            clip.duplicate_notes_by_id(note_ids, *params)

        def clip_select_notes(clip, params: Tuple[Any] = ()):
            self.logger.info("Calling method for %s: select_notes (params %s)" % (self.class_identifier, params))
            if len(params) == 4:
                pitch_start, pitch_span, time_start, time_span = params
            elif len(params) == 0:
                clip.select_all_notes()
                return
            else:
                raise ValueError("Invalid number of arguments for /clip/select/notes. Either 0 or 4 arguments must be passed.")
            notes = clip.get_notes_extended(pitch_start, pitch_span, time_start, time_span)
            note_ids = [n.note_id for n in notes]
            if len(note_ids) == 0:
                clip.deselect_all_notes()
                return
            clip.select_notes_by_id(note_ids)
        
        def clip_deselect_notes(clip, params: Tuple[Any] = ()):
            self.logger.info("Calling method for %s: deselect_notes (params %s)" % (self.class_identifier, params))
            if len(params) == 4:
                pitch_start, pitch_span, time_start, time_span = params
            elif len(params) == 0:
                clip.deselect_all_notes()
                return
            else:
                raise ValueError("Invalid number of arguments for /clip/deselect/notes. Either 0 or 4 arguments must be passed.")
            selected_notes = clip.get_selected_notes_extended()
            selected_ids = {n.note_id for n in selected_notes}
            deselect_notes = clip.get_notes_extended(pitch_start, pitch_span, time_start, time_span)
            deselect_ids = {n.note_id for n in deselect_notes}
            new_selection_ids = tuple(selected_ids - deselect_ids)
            clip.deselect_all_notes()
            if len(new_selection_ids) == 0:
                return
            clip.select_notes_by_id(new_selection_ids)

        
        # Not yet enabled, keeping for later
        def clip_apply_note_modifications(clip, params: Tuple[Any] = ()):
            self.logger.info("Calling method for %s: apply_note_modifications (params %s)" % (self.class_identifier, params))
            updates = {}
            note_ids = []
            for pitch, start_time, duration, velocity, mute, note_id, probability, velocity_deviation, release_velocity in _chunk(params, 9):
                updates[int(note_id)] = (pitch, start_time, duration, velocity, mute, probability, velocity_deviation, release_velocity)
                note_ids.append(int(note_id))
            notes = clip.get_notes_by_id(tuple(note_ids))
            for note in notes:
                note_id = int(note.note_id)
                if note_id not in updates:
                    continue
                pitch, start_time, duration, velocity, mute, probability, velocity_deviation, release_velocity = updates[note_id]
                note.pitch = pitch
                note.start_time = start_time
                note.duration = duration
                note.velocity = velocity
                note.mute = mute
                note.probability = probability
                note.velocity_deviation = velocity_deviation
                note.release_velocity = release_velocity
            clip.apply_note_modifications(notes)



        
        # Add Handlers
        local_funcs = locals()
        for method, spec in methods.items():
            alias = spec.get("alias")
            caller = spec.get("caller")
            # Skip disabled entries
            if not caller:
                continue
            # Custom methods
            elif not alias and isinstance(caller, str):
                target = local_funcs[caller]
                self.osc_server.add_handler("/live/clip/%s" % method,
                                            create_clip_callback(target))
                self.osc_server.add_handler("/live/arrangement_clip/%s" % method,
                                            create_arrangement_clip_callback(target))
            # Standard methods and aliases
            else:
                target = caller if alias else method
                self.osc_server.add_handler("/live/clip/%s" % method,
                                            create_clip_callback(self._call_method, target))
                self.osc_server.add_handler("/live/arrangement_clip/%s" % method,
                                            create_arrangement_clip_callback(self._call_method, target))

        for prop, spec in properties.items():
            getter_func = spec.get("get")
            if isinstance(getter_func, str):
                getter = local_funcs[getter_func]
                self.osc_server.add_handler("/live/clip/get/%s" % prop,
                                            create_clip_callback(getter))
                self.osc_server.add_handler("/live/arrangement_clip/get/%s" % prop,
                                            create_arrangement_clip_callback(getter))
            elif getter_func:
                self.osc_server.add_handler("/live/clip/get/%s" % prop,
                                            create_clip_callback(self._get_property, prop))
                self.osc_server.add_handler("/live/arrangement_clip/get/%s" % prop,
                                            create_arrangement_clip_callback(self._get_property, prop))
                
            setter_func = spec.get("set")
            if isinstance(setter_func, str):
                setter = local_funcs[setter_func]
                self.osc_server.add_handler("/live/clip/set/%s" % prop,
                                            create_clip_callback(setter))
                self.osc_server.add_handler("/live/arrangement_clip/set/%s" % prop,
                                            create_arrangement_clip_callback(setter))
            elif setter_func:
                self.osc_server.add_handler("/live/clip/set/%s" % prop,
                                            create_clip_callback(self._set_property, prop))
                self.osc_server.add_handler("/live/arrangement_clip/set/%s" % prop,
                                            create_arrangement_clip_callback(self._set_property, prop))
                
            observable = spec.get("listen")
            if isinstance(observable, str):
                getter = "bang" if observable == "bang" else local_funcs[observable]
                self.osc_server.add_handler("/live/clip/start_listen/%s" % prop,
                                            create_clip_callback(self._start_listen, prop, pass_clip_index=True, getter=getter))
                self.osc_server.add_handler("/live/clip/stop_listen/%s" % prop,
                                            create_clip_callback(self._stop_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/arrangement_clip/start_listen/%s" % prop,
                                            create_arrangement_clip_callback(self._start_listen, prop, pass_clip_index=True, getter=getter))
                self.osc_server.add_handler("/live/arrangement_clip/stop_listen/%s" % prop,
                                            create_arrangement_clip_callback(self._stop_listen, prop, pass_clip_index=True))
            elif observable:
                self.osc_server.add_handler("/live/clip/start_listen/%s" % prop,
                                            create_clip_callback(self._start_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/clip/stop_listen/%s" % prop,
                                            create_clip_callback(self._stop_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/arrangement_clip/start_listen/%s" % prop,
                                            create_arrangement_clip_callback(self._start_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/arrangement_clip/stop_listen/%s" % prop,
                                            create_arrangement_clip_callback(self._stop_listen, prop, pass_clip_index=True))

        # Global Clips Handlers
        
        def clips_filter_handler(params: Tuple):
            # TODO: Pre-cache clip notes
            if len(self._clip_notes_cache) == 0:
                self.logger.warning("Building clip notes cache...")
                self._build_clip_name_cache()
            else:
                self.logger.warning("Found existing clip notes cache (len = %d)" % len(self._clip_notes_cache))
            note_indices = [note_name_to_midi(name) for name in params]

            self.logger.warning("Got note indices: %s" % note_indices)
            for track_index, track in enumerate(self.song.tracks):
                for clip_slot_index, clip_slot in enumerate(track.clip_slots):
                    clip_notes_list = self._clip_notes_cache[track_index][clip_slot_index]
                    if clip_notes_list:
                        clip = clip_slot.clip
                        if all(note in note_indices for note in clip_notes_list):
                            clip.muted = False
                        else:
                            clip.muted = True

        self.osc_server.add_handler("/live/clips/filter", clips_filter_handler)

        def clips_unfilter_handler(params: Tuple):
            track_start = params[0] if len(params) > 0 else 0
            track_end = params[1] if len(params) > 1 else len(self.song.tracks)

            self.logger.info("Unfiltering tracks: %d .. %d" % (track_start, track_end))
            for track in self.song.tracks[track_start:track_end]:
                for clip_slot in track.clip_slots:
                    if clip_slot.has_clip:
                        clip = clip_slot.clip
                        clip.muted = False

        self.osc_server.add_handler("/live/clips/unfilter", clips_unfilter_handler)


    # Helpers
    
    def _build_clip_name_cache(self):
        regex = "([_-])([A-G][A-G#b1-9-]*)$"
        for track_index, track in enumerate(self.song.tracks):
            self._clip_notes_cache.append([])
            for clip_slot_index, clip_slot in enumerate(track.clip_slots):
                self._clip_notes_cache[-1].append([])
                if clip_slot.has_clip:
                    clip = clip_slot.clip
                    clip_name = clip.name
                    match = re.search(regex, clip_name)
                    if match:
                        clip_notes_str = match.group(2)
                        clip_notes_str = re.sub("[1-9]", "", clip_notes_str)
                        clip_notes_list = clip_notes_str.split("-")
                        clip_notes_list = [note_name_to_midi(name) for name in clip_notes_list]
                        self._clip_notes_cache[-1][-1] = clip_notes_list


class ClipViewHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "clip_view"

    def init_api(self):
        def create_clip_view_callback(func, *args, pass_clip_index=False):
            def view_callback(params: Tuple[Any]) -> Tuple:
                track_index, clip_index = int(params[0]), int(params[1])
                track = self.song.tracks[track_index]
                clip = track.clip_slots[clip_index].clip
                view = clip.view
                if pass_clip_index:
                    rv = func(view, *args, tuple(params[0:]))
                else:
                    rv = func(view, *args, tuple(params[2:]))
                if rv is not None:
                    return (track_index, clip_index, *rv)
            return view_callback

        def create_arrangement_clip_view_callback(func, *args, pass_clip_index=False):
            def view_callback(params: Tuple[Any]) -> Tuple:
                track_index, clip_index = int(params[0]), int(params[1])
                track = self.song.tracks[track_index]
                clip = track.arrangement_clips[clip_index]
                view = clip.view
                if pass_clip_index:
                    rv = func(view, *args, tuple(params[0:]))
                else:
                    rv = func(view, *args, tuple(params[2:]))
                if rv is not None:
                    return (track_index, clip_index, *rv)
            return view_callback

        methods = {
            "show/loop":                 {"alias": 1, "caller": "show_loop"},
            "show/envelope":             {"alias": 1, "caller": "show_envelope"},
            "hide/envelope":             {"alias": 1, "caller": "hide_envelope"},
            "select/envelope_parameter": {"alias": 0, "caller": None},  # TODO: Need to to target device parameter in envelope view
        }

        properties = {
            "canonical_parent":  {"get": 0, "set": 0, "listen": 0},  # TODO: Clip object: Not serializable
            "grid_is_triplet":   {"get": 1, "set": 1, "listen": 0},
            "grid_quantization": {"get": 1, "set": 1, "listen": 0},  # {'8_bars': 1, '4_bars': 2, '2_bars': 3, 'bar': 4, 'half': 5, 'quarter': 6, 'eighth': 7, 'sixteenth': 8, 'thirtysecond': 9}
        }
        
        # Add Handlers
        for method, spec in methods.items():
            caller = spec.get("caller")
            alias = spec.get("alias")
            if not caller:
                continue
            else:
                target = caller if alias else method
                self.osc_server.add_handler("/live/clip/view/%s" % method,
                                            create_clip_view_callback(self._call_method, target))
                self.osc_server.add_handler("/live/arrangement_clip/view/%s" % method,
                                            create_arrangement_clip_view_callback(self._call_method, target))

        for prop, spec in properties.items():
            getter_func = spec.get("get")
            if getter_func:
                self.osc_server.add_handler("/live/clip/view/get/%s" % prop,
                                            create_clip_view_callback(self._get_property, prop))
                self.osc_server.add_handler("/live/arrangement_clip/view/get/%s" % prop,
                                            create_arrangement_clip_view_callback(self._get_property, prop))

            setter_func = spec.get("set")
            if setter_func:
                self.osc_server.add_handler("/live/clip/view/set/%s" % prop,
                                            create_clip_view_callback(self._set_property, prop))
                self.osc_server.add_handler("/live/arrangement_clip/view/set/%s" % prop,
                                            create_arrangement_clip_view_callback(self._set_property, prop))

            listen_func = spec.get("listen")
            if listen_func:
                self.osc_server.add_handler("/live/clip/view/start_listen/%s" % prop,
                                            create_clip_view_callback(self._start_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/clip/view/stop_listen/%s" % prop,
                                            create_clip_view_callback(self._stop_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/arrangement_clip/view/start_listen/%s" % prop,
                                            create_arrangement_clip_view_callback(self._start_listen, prop, pass_clip_index=True))
                self.osc_server.add_handler("/live/arrangement_clip/view/stop_listen/%s" % prop,
                                            create_arrangement_clip_view_callback(self._stop_listen, prop, pass_clip_index=True))
