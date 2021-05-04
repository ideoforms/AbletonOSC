from functools import partial
from typing import Optional, Tuple, Any
from .component import AbletonOSCComponent

import logging

logger = logging.getLogger("abletonosc")

class SongComponent(AbletonOSCComponent):
    def init_api(self):
        #--------------------------------------------------------------------------------
        # Generic callbacks
        #--------------------------------------------------------------------------------
        def call_method(method, address, params):
            logger.info("Calling method: %s (params %s)" % (method, str(params)))
            getattr(self.song, method)(*params)

        def set_property(prop, address: str, params: Optional[Tuple[Any]]) -> None:
            logger.info("Setting property: %s (new value %s)" % (prop, params[0]))
            setattr(self.song, prop, params[0])

        def get_property(prop, address, params) -> Tuple[Any]:
            logger.info("Getting property: %s" % prop)
            return getattr(self.song, prop),

        def start_property_listen(prop, address: str, params: Optional[Tuple[Any]]) -> None:
            def property_changed_callback():
                value = getattr(self.song, prop)
                logger.info("Property %s changed: %s" % (prop, value))
                osc_address = "/live/set/get_property/%s" % prop
                self.osc_server.send(osc_address, (value,))

            add_listener_function_name = "add_%s_listener" % prop
            add_listener_function = getattr(self.song, add_listener_function_name)
            add_listener_function(property_changed_callback)
            self.listener_functions[prop] = property_changed_callback

        def stop_property_listen(prop, address: str, params: Optional[Tuple[Any]]) -> None:
            if prop in self.listener_functions:
                listener_function = self.listener_functions[prop]
                remove_listener_function_name = "remove_%s_listener" % prop
                remove_listener_function = getattr(self.song, remove_listener_function_name)
                remove_listener_function(listener_function)
                del self.listener_functions[prop]
            else:
                logger.warning("No listener function found for property: %s" % prop)

        #--------------------------------------------------------------------------------
        # Init callbacks for Set: methods
        #--------------------------------------------------------------------------------
        for method in [
            "start_playing",
            "stop_playing",
            "continue_playing",
            "stop_all_clips",
            "create_audio_track",
            "create_midi_track",
            "create_return_track",
            "create_scene",
            "jump_by"
        ]:
            callback = partial(call_method, method)
            self.osc_server.add_handler("/live/set/%s" % method, callback)

        #--------------------------------------------------------------------------------
        # Init callbacks for Set: properties
        #--------------------------------------------------------------------------------
        properties_rw = [
            "arrangement_overdub",
            "back_to_arranger",
            "clip_trigger_quantization",
            "current_song_time",
            "groove_amount",
            "loop",
            "loop_length",
            "loop_start",
            "metronome",
            "midi_recording_quantization",
            "nudge_down",
            "nudge_up",
            "punch_in",
            "punch_out",
            "record_mode"
        ]
        properties_r = [
            "is_playing"
        ]

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/set/get_property/%s" % prop, partial(get_property, prop))
            self.osc_server.add_handler("/live/set/start_property_listen/%s" % prop, partial(start_property_listen, prop))
            self.osc_server.add_handler("/live/set/stop_property_listen/%s" % prop, partial(stop_property_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/set/set_property/%s" % prop, partial(set_property, prop))
