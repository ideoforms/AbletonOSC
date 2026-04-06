import re
from typing import Tuple, Callable, Any, Optional
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

class ClipHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "clip"
        self._clip_notes_cache = []

    def init_api(self):
        def create_clip_callback(func, *args, pass_clip_index=False):
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
                    rv = func(clip, *args, tuple(params[0:]))
                else:
                    rv = func(clip, *args, tuple(params[2:]))

                if rv is not None:
                    return (track_index, clip_index, *rv)

            return clip_callback

        methods = [
            "crop",
            "deselect_all_notes",
            "duplicate_loop",
            "fire",
            "quantize",
            "remove_notes_by_id",
            "select_all_notes",
            "stop",
        ]
        properties_r = [
            "end_time",
            "file_path",
            "gain_display_string",
            "has_groove",
            "is_arrangement_clip",
            "is_audio_clip",
            "is_midi_clip",
            "is_overdubbing",
            "is_playing",
            "is_recording",
            "is_triggered",
            "length",
            "playing_position",
            "sample_length",
            "sample_rate",
            "signature_denominator",
            "signature_numerator",
            "start_time",
            "will_record_on_start",
        ]
        properties_rw = [
            "color",
            "color_index",
            "end_marker",
            "gain",
            "launch_mode",
            "launch_quantization",
            "legato",
            "loop_end",
            "loop_start",
            "looping",
            "muted",
            "name",
            "pitch_coarse",
            "pitch_fine",
            "position",
            "ram_mode",
            "start_marker",
            "velocity_amount",
            "warp_mode",
            "warping",
        ]

        for method in methods:
            self.osc_server.add_handler("/live/clip/%s" % method,
                                        create_clip_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/clip/get/%s" % prop,
                                        create_clip_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/clip/start_listen/%s" % prop,
                                        create_clip_callback(self._start_listen, prop, pass_clip_index=True))
            self.osc_server.add_handler("/live/clip/stop_listen/%s" % prop,
                                        create_clip_callback(self._stop_listen, prop, pass_clip_index=True))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/clip/set/%s" % prop,
                                        create_clip_callback(self._set_property, prop))

        def clip_get_notes(clip, params: Tuple[Any] = ()):
            if len(params) == 4:
                pitch_start, pitch_span, time_start, time_span = params
            elif len(params) == 0:
                pitch_start, pitch_span, time_start, time_span = 0, 127, -8192, 16384
            else:
                raise ValueError("Invalid number of arguments for /clip/get/notes. Either 0 or 4 arguments must be passed.")
            notes = clip.get_notes_extended(pitch_start, pitch_span, time_start, time_span)
            all_note_attributes = []
            for note in notes:
                all_note_attributes += [note.pitch, note.start_time, note.duration, note.velocity, note.mute]
            return tuple(all_note_attributes)

        def clip_add_notes(clip, params: Tuple[Any] = ()):
            notes = []
            for offset in range(0, len(params), 5):
                pitch, start_time, duration, velocity, mute = params[offset:offset + 5]
                note = Live.Clip.MidiNoteSpecification(start_time=start_time,
                                                       duration=duration,
                                                       pitch=pitch,
                                                       velocity=velocity,
                                                       mute=mute)
                notes.append(note)
            clip.add_new_notes(tuple(notes))

        def clip_remove_notes(clip, params: Tuple[Any] = ()):
            if len(params) == 4:
                pitch_start, pitch_span, time_start, time_span = params
            elif len(params) == 0:
                pitch_start, pitch_span, time_start, time_span = 0, 127, -8192, 16384
            else:
                raise ValueError("Invalid number of arguments for /clip/remove/notes. Either 0 or 4 arguments must be passed.")
            clip.remove_notes_extended(pitch_start, pitch_span, time_start, time_span)

        self.osc_server.add_handler("/live/clip/get/notes", create_clip_callback(clip_get_notes))
        self.osc_server.add_handler("/live/clip/add/notes", create_clip_callback(clip_add_notes))
        self.osc_server.add_handler("/live/clip/remove/notes", create_clip_callback(clip_remove_notes))

        #--------------------------------------------------------------------------------
        # Extended notes: 8 fields per note (pitch, start, dur, vel, mute,
        # probability, velocity_deviation, release_velocity)
        #--------------------------------------------------------------------------------
        def clip_get_notes_extended(clip, params: Tuple[Any] = ()):
            if len(params) == 4:
                pitch_start, pitch_span, time_start, time_span = params
            elif len(params) == 0:
                pitch_start, pitch_span, time_start, time_span = 0, 127, -8192, 16384
            else:
                raise ValueError("Invalid args for get/notes_extended: 0 or 4 required")
            notes = clip.get_notes_extended(pitch_start, pitch_span, time_start, time_span)
            result = []
            for note in notes:
                result += [
                    note.pitch, note.start_time, note.duration, note.velocity, note.mute,
                    getattr(note, 'probability', 1.0),
                    getattr(note, 'velocity_deviation', 0.0),
                    getattr(note, 'release_velocity', 64),
                ]
            return tuple(result)

        def clip_add_notes_extended(clip, params: Tuple[Any] = ()):
            notes = []
            for offset in range(0, len(params), 8):
                if offset + 7 >= len(params):
                    break
                try:
                    spec = Live.Clip.MidiNoteSpecification(
                        pitch=int(params[offset]),
                        start_time=float(params[offset + 1]),
                        duration=float(params[offset + 2]),
                        velocity=float(params[offset + 3]),
                        mute=bool(int(params[offset + 4])),
                        probability=float(params[offset + 5]),
                        velocity_deviation=float(params[offset + 6]),
                        release_velocity=int(params[offset + 7]),
                    )
                except TypeError:
                    # Fallback for Live versions without extended note support
                    spec = Live.Clip.MidiNoteSpecification(
                        pitch=int(params[offset]),
                        start_time=float(params[offset + 1]),
                        duration=float(params[offset + 2]),
                        velocity=float(params[offset + 3]),
                        mute=bool(int(params[offset + 4])),
                    )
                notes.append(spec)
            if notes:
                clip.add_new_notes(tuple(notes))

        self.osc_server.add_handler("/live/clip/get/notes_extended", create_clip_callback(clip_get_notes_extended))
        self.osc_server.add_handler("/live/clip/add/notes_extended", create_clip_callback(clip_add_notes_extended))

        #--------------------------------------------------------------------------------
        # Warp markers (audio clips only)
        #--------------------------------------------------------------------------------
        def clip_get_warp_markers(clip, params: Tuple[Any] = ()):
            markers = list(clip.warp_markers)
            result = []
            # Drop the trailing shadow marker
            for marker in markers[:-1] if len(markers) > 1 else markers:
                result.append(marker.beat_time)
                result.append(marker.sample_time)
            return tuple(result)

        def clip_add_warp_marker(clip, params: Tuple[Any] = ()):
            beat_time, sample_time = float(params[0]), float(params[1])
            # Live 12: WarpMarker(sample_time, beat_time) — note: sample_time first
            marker = Live.Clip.WarpMarker(sample_time, beat_time)
            clip.add_warp_marker(marker)

        def clip_move_warp_marker(clip, params: Tuple[Any] = ()):
            marker_index = int(params[0])
            new_beat_time = float(params[1])
            markers = list(clip.warp_markers)
            if marker_index < len(markers) - 1:
                clip.move_warp_marker(markers[marker_index].beat_time, new_beat_time)

        def clip_remove_warp_marker(clip, params: Tuple[Any] = ()):
            marker_index = int(params[0])
            markers = list(clip.warp_markers)
            if marker_index < len(markers) - 1:
                clip.remove_warp_marker(markers[marker_index].beat_time)

        self.osc_server.add_handler("/live/clip/get/warp_markers", create_clip_callback(clip_get_warp_markers))
        self.osc_server.add_handler("/live/clip/add/warp_marker", create_clip_callback(clip_add_warp_marker))
        self.osc_server.add_handler("/live/clip/move/warp_marker", create_clip_callback(clip_move_warp_marker))
        self.osc_server.add_handler("/live/clip/remove/warp_marker", create_clip_callback(clip_remove_warp_marker))

        #--------------------------------------------------------------------------------
        # Time conversion (beats <-> samples)
        #--------------------------------------------------------------------------------
        def clip_convert_time(clip, params: Tuple[Any] = ()):
            time_value = float(params[0])
            from_unit = str(params[1])
            to_unit = str(params[2])
            if from_unit == "beats" and to_unit == "samples":
                return (clip.beat_to_sample_time(time_value),)
            elif from_unit == "samples" and to_unit == "beats":
                return (clip.sample_to_beat_time(time_value),)
            elif from_unit == to_unit:
                return (time_value,)
            else:
                raise ValueError("Unsupported conversion: %s to %s" % (from_unit, to_unit))

        self.osc_server.add_handler("/live/clip/convert/time", create_clip_callback(clip_convert_time))

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
