import Live
from typing import Tuple
from .handler import AbletonOSCHandler

class ApplicationHandler(AbletonOSCHandler):
    def init_api(self):
        #--------------------------------------------------------------------------------
        # Generic callbacks
        #--------------------------------------------------------------------------------
        def get_version(_) -> Tuple:
            application = Live.Application.get_application()
            return application.get_major_version(), application.get_minor_version()
        self.osc_server.add_handler("/live/application/get/version", get_version)
        self.osc_server.send("/live/startup")

        def get_average_process_usage(_) -> Tuple:
            application = Live.Application.get_application()
            return application.average_process_usage,
        self.osc_server.add_handler("/live/application/get/average_process_usage", get_average_process_usage)
        self.osc_server.send("/live/application/get/average_process_usage")

        #--------------------------------------------------------------------------------
        # View controls
        #--------------------------------------------------------------------------------
        def get_focused_document_view(_) -> Tuple:
            application = Live.Application.get_application()
            return (application.view.focused_document_view,)
        self.osc_server.add_handler("/live/application/get/focused_document_view", get_focused_document_view)

        def focus_view(params) -> Tuple:
            """Focus a view by name (e.g., 'Session', 'Arranger', 'Detail/Clip')"""
            application = Live.Application.get_application()
            view_name = params[0] if params else 'Session'
            application.view.focus_view(view_name)
            return ("success", view_name)
        self.osc_server.add_handler("/live/application/focus_view", focus_view)

        def show_view(params) -> Tuple:
            """Show a view by name"""
            application = Live.Application.get_application()
            view_name = params[0] if params else 'Session'
            application.view.show_view(view_name)
            return ("success", view_name)
        self.osc_server.add_handler("/live/application/show_view", show_view)
