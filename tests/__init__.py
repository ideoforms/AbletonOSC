import time
import pytest
import threading
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from typing import Callable, Iterable

CLIENT_PORT = 11000
SERVER_PORT = 11001

# Live tick is 100ms. Wait for this long plus a short additional buffer.
TICK_DURATION = 0.125

class AbletonOSCClient:
    def __init__(self):
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self.handle_osc)
        self.server = ThreadingOSCUDPServer(("127.0.0.1", SERVER_PORT), dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.client = SimpleUDPClient("127.0.0.1", CLIENT_PORT)
        self.address_handlers = {}

    def handle_osc(self, address, *params):
        if address in self.address_handlers:
            self.address_handlers[address](params)

    def stop(self):
        self.server.shutdown()
        self.server_thread.join()
        self.server = None

    def send_message(self,
                     address: str,
                     params: Iterable = ()):
        self.client.send_message(address, params)

    def add_handler(self,
                    address: str,
                    fn: Callable = None):
        self.address_handlers[address] = fn

    def remove_handler(self,
                       address: str):
        del self.address_handlers[address]

    def await_reply(self,
                    address: str,
                    fn: Callable = None,
                    timeout: float = TICK_DURATION):
        """
        Awaits a reply from the given `address`, and optionally asserts that the function `fn`
        returns True when called with the returned OSC parameters.

        Args:
            address: OSC query (and reply) address
            fn: Optional assertion function
            timeout: Maximum number of seconds to wait for a successful reply

        Returns:
            True if the reply is received within the timeout period and the assertion succeeds,
            False otherwise

        """
        _event = threading.Event()

        def received_response(params):
            print("Received response: %s" % str(params))
            nonlocal _event
            if fn is None or fn(params):
                _event.set()

        self.add_handler(address, received_response)
        _event.wait(timeout)
        self.remove_handler(address)
        return _event.is_set()

    def query_and_await(self,
                        address: str,
                        params: tuple = (),
                        fn: Callable = None,
                        timeout = TICK_DURATION):
        _event = threading.Event()

        def received_response(params):
            nonlocal _event
            if fn is None or fn(params):
                _event.set()

        self.add_handler(address, received_response)
        self.send_message(address, params)
        _event.wait(timeout)
        self.remove_handler(address)
        return _event.is_set()

@pytest.fixture(scope="module")
def client() -> AbletonOSCClient:
    client = AbletonOSCClient()
    yield client
    client.stop()

def wait_one_tick():
    """
    Sleep for one Ableton Live tick (100ms).
    """
    time.sleep(TICK_DURATION)
