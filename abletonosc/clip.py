from functools import partial
from typing import Optional, Tuple, Any
from .component import AbletonOSCComponent

import Live
import logging

logger = logging.getLogger("abletonosc")

class ClipComponent(AbletonOSCComponent):
    def init_api(self):
        def clip_command(func):
            def clip_command_wrapper(address, params: Tuple[Any]):
                track_index, clip_index = params[:2]
                track = self.song.tracks[track_index]
                clip_slot = track.clip_slots[clip_index]
                return func(clip_slot, params[2:])

            return clip_command_wrapper

        @clip_command
        def clip_create(clip_slot, params: Tuple[Any]):
            clip_length = params[0]
            clip_slot.create_clip(clip_length)

        @clip_command
        def clip_delete(clip_slot, params: Tuple[Any]):
            clip_slot.delete_clip()

        @clip_command
        def clipslot_has_clip(clip_slot, params: Tuple[Any]):
            return (clip_slot.has_clip,)

        @clip_command
        def clip_slot_fire(clip_slot, params: Tuple[Any]):
            clip_slot.fire()

        @clip_command
        def clip_slot_stop(clip_slot, params: Tuple[Any]):
            clip_slot.stop()

        @clip_command
        def clip_set_color(clip_slot, params: Tuple[Any]):
            clip_slot.clip.color = params[0]

        @clip_command
        def clip_get_is_midi_clip(clip_slot, params: Tuple[Any]):
            return (clip_slot.clip.is_midi_clip,)

        @clip_command
        def clip_add_new_note(clip_slot, params: Tuple[Any]):
            start_time, duration, pitch, velocity, mute = params
            note = Live.Clip.MidiNoteSpecification(start_time=start_time,
                                                   duration=duration,
                                                   pitch=pitch,
                                                   velocity=velocity,
                                                   mute=mute)
            clip_slot.clip.clip.add_new_notes((note,))

        self.osc_server.add_handler("/live/clip/create", clip_create)
        self.osc_server.add_handler("/live/clip/delete", clip_delete)
        self.osc_server.add_handler("/live/clip/fire", clip_slot_fire)
        self.osc_server.add_handler("/live/clip/stop", clip_slot_stop)
        self.osc_server.add_handler("/live/clip/set/color", clip_set_color)
        self.osc_server.add_handler("/live/clip/get/is_midi_clip", clip_get_is_midi_clip)
        self.osc_server.add_handler("/live/clip/get/has_clip", clipslot_has_clip)
        self.osc_server.add_handler("/live/clip/add_new_note", clip_add_new_note)