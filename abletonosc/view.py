from functools import partial
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler
import Live

class ViewHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "view"

    def init_api(self):
        def get_selected_scene(params: Optional[Tuple] = ()):
            return (list(self.song.scenes).index(self.song.view.selected_scene),)

        def get_selected_track(params: Optional[Tuple] = ()):
            return (list(self.song.tracks).index(self.song.view.selected_track),)

        def get_selected_clip(params: Optional[Tuple] = ()):
            return (get_selected_track()[0], get_selected_scene()[0])
        
        def get_selected_device(params: Optional[Tuple] = ()):
            return (get_selected_track()[0], list(self.song.view.selected_track.devices).index(self.song.view.selected_track.view.selected_device))

        def set_selected_scene(params: Optional[Tuple] = ()):
            self.song.view.selected_scene = self.song.scenes[params[0]]

        def set_selected_track(params: Optional[Tuple] = ()):
            self.song.view.selected_track = self.song.tracks[params[0]]

        def set_selected_clip(params: Optional[Tuple] = ()):
            set_selected_track((params[0],))
            set_selected_scene((params[1],))

        def set_selected_device(params: Optional[Tuple] = ()):
            device = self.song.tracks[params[0]].devices[params[1]]
            self.song.view.select_device(device)
            return params[0], params[1]

        def show_clip_envelope(params: Optional[Tuple] = ()):
            """
            Focuses Clip View and shows the Envelopes box for the clip currently
            displayed there.
            """
            clip = self.song.view.detail_clip
            if clip is None:
                raise RuntimeError("No clip is currently shown in Clip View")

            Live.Application.get_application().view.focus_view("Detail/Clip")
            clip.view.show_envelope()

        def hide_clip_envelope(params: Optional[Tuple] = ()):
            """
            Hides the Envelopes box for the clip currently shown in Clip View,
            returning it to the Sample (or Notes) editor.
            """
            clip = self.song.view.detail_clip
            if clip is None:
                raise RuntimeError("No clip is currently shown in Clip View")

            clip.view.hide_envelope()

        def nudge_clip_transposition(params: Optional[Tuple] = ()):
            """
            Adds params[0] semitones to the pitch_coarse of the clip currently shown in
            Clip View, clamped to Live's -48..48 range. Returns the new value.
            """
            clip = self.song.view.detail_clip
            if clip is None:
                raise RuntimeError("No clip is currently shown in Clip View")
            if not clip.is_audio_clip:
                raise RuntimeError("Transposition only applies to audio clips")

            new_value = max(-48, min(48, clip.pitch_coarse + int(params[0])))
            clip.pitch_coarse = new_value
            return (new_value,)

        def set_clip_transposition(params: Optional[Tuple] = ()):
            """
            Sets the pitch_coarse of the clip currently shown in Clip View to params[0]
            semitones, clamped to Live's -48..48 range. Returns the new value.

            Note: this sets the clip's scalar transposition. If a Transposition
            envelope has already been drawn on the clip, the drawn curve still
            determines playback -- Live's API has no way to clear a single warp
            parameter's envelope (only clip.clear_all_envelopes(), which removes
            every envelope on the clip, including unrelated ones).
            """
            clip = self.song.view.detail_clip
            if clip is None:
                raise RuntimeError("No clip is currently shown in Clip View")
            if not clip.is_audio_clip:
                raise RuntimeError("Transposition only applies to audio clips")

            new_value = max(-48, min(48, int(params[0])))
            clip.pitch_coarse = new_value
            return (new_value,)

        self.osc_server.add_handler("/live/view/show_clip_envelope", show_clip_envelope)
        self.osc_server.add_handler("/live/view/hide_clip_envelope", hide_clip_envelope)
        self.osc_server.add_handler("/live/view/nudge_clip_transposition", nudge_clip_transposition)
        self.osc_server.add_handler("/live/view/set_clip_transposition", set_clip_transposition)

        self.osc_server.add_handler("/live/view/get/selected_scene", get_selected_scene)
        self.osc_server.add_handler("/live/view/get/selected_track", get_selected_track)
        self.osc_server.add_handler("/live/view/get/selected_clip", get_selected_clip)
        self.osc_server.add_handler("/live/view/get/selected_device", get_selected_device)
        self.osc_server.add_handler("/live/view/set/selected_scene", set_selected_scene)
        self.osc_server.add_handler("/live/view/set/selected_track", set_selected_track)
        self.osc_server.add_handler("/live/view/set/selected_clip", set_selected_clip)
        self.osc_server.add_handler("/live/view/set/selected_device", set_selected_device)
        
        self.osc_server.add_handler('/live/view/start_listen/selected_scene', partial(self._start_listen, self.song.view, "selected_scene", getter=get_selected_scene))
        self.osc_server.add_handler('/live/view/start_listen/selected_track', partial(self._start_listen, self.song.view, "selected_track", getter=get_selected_track))
        self.osc_server.add_handler('/live/view/stop_listen/selected_scene', partial(self._stop_listen, self.song.view, "selected_scene"))
        self.osc_server.add_handler('/live/view/stop_listen/selected_track', partial(self._stop_listen, self.song.view, "selected_track"))
