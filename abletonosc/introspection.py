from typing import Tuple, Any
from .handler import AbletonOSCHandler

class IntrospectionHandler(AbletonOSCHandler):
    """
    Handler for introspecting Live objects via OSC.
    Provides API discovery for any Live object type.
    """

    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "introspect"

    def init_api(self):
        """
        Initialize the introspection API endpoint.
        Endpoint: /live/introspect <object_type> <object_ids...>
        """
        def introspect_callback(params: Tuple[Any]):
            """
            Handle introspection requests for any Live object type.

            Args:
                params: Tuple containing (object_type, object_ids...)
                       e.g., ("device", 2, 2) or ("clip", 0, 1)
            """
            if len(params) < 1:
                self.logger.error("Introspect: No object type specified")
                return

            object_type = params[0]
            object_ids = params[1:]

            # Get the appropriate Live object based on type
            try:
                if object_type == "device":
                    if len(object_ids) < 2:
                        self.logger.error("Introspect device: Missing track_id or device_id")
                        return
                    track_index, device_index = int(object_ids[0]), int(object_ids[1])
                    obj = self.song.tracks[track_index].devices[device_index]

                elif object_type == "clip":
                    if len(object_ids) < 2:
                        self.logger.error("Introspect clip: Missing track_id or clip_id")
                        return
                    track_index, clip_index = int(object_ids[0]), int(object_ids[1])
                    obj = self.song.tracks[track_index].clip_slots[clip_index].clip

                elif object_type == "track":
                    if len(object_ids) < 1:
                        self.logger.error("Introspect track: Missing track_id")
                        return
                    track_index = int(object_ids[0])
                    obj = self.song.tracks[track_index]

                elif object_type == "song":
                    obj = self.song

                else:
                    self.logger.error(f"Introspect: Unknown object type '{object_type}'")
                    return

            except (IndexError, AttributeError) as e:
                self.logger.error(f"Introspect: Failed to access {object_type} with IDs {object_ids}: {e}")
                return

            # Perform introspection on the object
            result = self._introspect_object(obj)

            # Return object_ids followed by introspection data
            return (*object_ids, *result)

        self.osc_server.add_handler("/live/introspect", introspect_callback)

    def _introspect_object(self, obj) -> Tuple[str, ...]:
        """
        Introspect a Live object and return its properties and methods.

        Args:
            obj: The Live object to introspect

        Returns:
            Tuple containing: ("properties:", prop1, prop2, ..., "methods:", method1, method2, ...)
        """
        all_attrs = dir(obj)

        # Filter out private/magic methods and common inherited methods
        filtered_attrs = [
            attr for attr in all_attrs
            if not attr.startswith('_') and attr not in ['add_update_listener', 'remove_update_listener']
        ]

        properties = []
        methods = []

        for attr in filtered_attrs:
            try:
                attr_obj = getattr(obj, attr)
                # Check if it's callable (method) or a property
                if callable(attr_obj):
                    methods.append(attr)
                else:
                    # Try to get the value to see if it's a readable property
                    try:
                        # Limit string length to avoid OSC message size issues
                        # and improve readability in introspection output
                        value = str(attr_obj)[:50]
                        properties.append(f"{attr}={value}")
                    except:
                        properties.append(attr)
            except:
                pass

        # Return as tuples for OSC transmission (lowercase for consistency)
        return (
            "properties:", *properties,
            "methods:", *methods
        )