from typing import Tuple, Any
from .handler import AbletonOSCHandler
import Live
import logging

logger = logging.getLogger("abletonosc")


class ArrangementHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "arrangement"

    def init_api(self):
        def create_midi_clip(params: Tuple[Any]):
            """
            Create an empty MIDI clip in the arrangement view.
            /live/arrangement/create_midi_clip (track, start_time, length)
            Requires Live 12.2+
            """
            track, track_id = self._resolve_track(params[0])
            start_time = float(params[1])
            length = float(params[2])

            track.create_midi_clip(start_time, length)

            logger.info("Created arrangement MIDI clip on track %s at beat %.1f, length %.1f" %
                        (track_id, start_time, length))
            return (track_id, start_time, length)

        def duplicate_to_arrangement(params: Tuple[Any]):
            """
            Copy a session clip to the arrangement at a specific beat position.
            /live/arrangement/duplicate_to_arrangement (track, clip_slot_index, destination_time)
            """
            track, track_id = self._resolve_track(params[0])
            clip_slot_index = int(params[1])
            destination_time = float(params[2])

            if not hasattr(track, 'clip_slots'):
                raise ValueError("Track %s has no clip slots" % track_id)

            clip_slot = track.clip_slots[clip_slot_index]

            if not clip_slot.has_clip:
                raise ValueError("No clip in slot %d on track %s" % (clip_slot_index, track_id))

            clip = clip_slot.clip
            track.duplicate_clip_to_arrangement(clip, destination_time)

            logger.info("Duplicated session clip (track %s, slot %d) to arrangement at beat %.1f" %
                        (track_id, clip_slot_index, destination_time))
            return (track_id, clip_slot_index, destination_time)

        def delete_clip(params: Tuple[Any]):
            """
            Delete an arrangement clip.
            /live/arrangement/delete_clip (track, clip_index)
            """
            track, track_id = self._resolve_track(params[0])
            clip_index = int(params[1])

            clips = track.arrangement_clips

            if clip_index >= len(clips):
                raise ValueError("Clip index %d out of range (track has %d arrangement clips)" %
                                 (clip_index, len(clips)))

            clip = clips[clip_index]
            track.delete_clip(clip)

            logger.info("Deleted arrangement clip %d on track %s" % (clip_index, track_id))
            return (track_id, clip_index)

        def get_clips(params: Tuple[Any]):
            """
            List arrangement clips for a track.
            /live/arrangement/get/clips (track)
            Returns: (track_id, name, start_time, length, is_midi, ...)
            """
            track, track_id = self._resolve_track(params[0])
            clips = track.arrangement_clips

            result = [track_id]
            for clip in clips:
                try:
                    result.append(clip.name)
                    result.append(clip.start_time)
                    result.append(clip.length)
                    result.append(1 if clip.is_midi_clip else 0)
                except Exception as e:
                    logger.warning("Error reading arrangement clip: %s" % e)
                    continue

            return tuple(result)

        def get_notes(params: Tuple[Any]):
            """
            Get MIDI notes from an arrangement clip.
            /live/arrangement/get/notes (track, clip_index, [start_pitch, pitch_span, start_time, time_span])
            """
            track, track_id = self._resolve_track(params[0])
            clip_index = int(params[1])
            clips = track.arrangement_clips

            if clip_index >= len(clips):
                raise ValueError("Clip index %d out of range" % clip_index)

            clip = clips[clip_index]
            if not clip.is_midi_clip:
                raise ValueError("Clip at index %d is not a MIDI clip" % clip_index)

            if len(params) >= 6:
                from_pitch = int(params[2])
                pitch_span = int(params[3])
                from_time = float(params[4])
                time_span = float(params[5])
            else:
                from_pitch = 0
                pitch_span = 128
                from_time = 0.0
                time_span = clip.length

            notes = clip.get_notes_extended(from_pitch, pitch_span, from_time, time_span)

            result = [track_id, clip_index]
            for note in notes:
                result.append(note.pitch)
                result.append(note.start_time)
                result.append(note.duration)
                result.append(note.velocity)
                result.append(1 if note.mute else 0)

            return tuple(result)

        def add_notes(params: Tuple[Any]):
            """
            Add MIDI notes to an arrangement clip.
            /live/arrangement/add/notes (track, clip_index, pitch, start, duration, velocity, mute, ...)
            """
            track, track_id = self._resolve_track(params[0])
            clip_index = int(params[1])
            clips = track.arrangement_clips

            if clip_index >= len(clips):
                raise ValueError("Clip index %d out of range" % clip_index)

            clip = clips[clip_index]
            if not clip.is_midi_clip:
                raise ValueError("Clip at index %d is not a MIDI clip" % clip_index)

            note_params = params[2:]
            notes = []
            for i in range(0, len(note_params), 5):
                if i + 4 >= len(note_params):
                    break
                spec = Live.Clip.MidiNoteSpecification(
                    pitch=int(note_params[i]),
                    start_time=float(note_params[i + 1]),
                    duration=float(note_params[i + 2]),
                    velocity=float(note_params[i + 3]),
                    mute=bool(int(note_params[i + 4]))
                )
                notes.append(spec)

            if notes:
                clip.add_new_notes(tuple(notes))
                logger.info("Added %d notes to arrangement clip %d on track %s" %
                            (len(notes), clip_index, track_id))

            return (track_id, clip_index, len(notes))

        def remove_notes(params: Tuple[Any]):
            """
            Remove notes from an arrangement clip by range.
            /live/arrangement/remove/notes (track, clip_index, [from_pitch, pitch_span, from_time, time_span])
            """
            track, track_id = self._resolve_track(params[0])
            clip_index = int(params[1])
            clips = track.arrangement_clips

            if clip_index >= len(clips):
                raise ValueError("Clip index %d out of range" % clip_index)

            clip = clips[clip_index]
            if not clip.is_midi_clip:
                raise ValueError("Clip at index %d is not a MIDI clip" % clip_index)

            if len(params) >= 6:
                from_pitch = int(params[2])
                pitch_span = int(params[3])
                from_time = float(params[4])
                time_span = float(params[5])
            else:
                from_pitch = 0
                pitch_span = 128
                from_time = 0.0
                time_span = clip.length

            clip.remove_notes_extended(from_pitch, pitch_span, from_time, time_span)
            logger.info("Removed notes from arrangement clip %d on track %s" % (clip_index, track_id))
            return (track_id, clip_index)

        self.osc_server.add_handler("/live/arrangement/create_midi_clip", create_midi_clip)
        self.osc_server.add_handler("/live/arrangement/duplicate_to_arrangement", duplicate_to_arrangement)
        self.osc_server.add_handler("/live/arrangement/delete_clip", delete_clip)
        self.osc_server.add_handler("/live/arrangement/get/clips", get_clips)
        self.osc_server.add_handler("/live/arrangement/get/notes", get_notes)
        self.osc_server.add_handler("/live/arrangement/add/notes", add_notes)
        self.osc_server.add_handler("/live/arrangement/remove/notes", remove_notes)
