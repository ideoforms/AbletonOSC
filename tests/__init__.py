import time
import pytest
import threading
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from typing import Callable

CLIENT_PORT = 11000
SERVER_PORT = 11001

# Live tick is 100ms. Wait for this long plus a short additional buffer.
TICK_DURATION = 0.11

@pytest.fixture(scope="module")
def server() -> ThreadingOSCUDPServer:
    dispatcher = Dispatcher()
    server = ThreadingOSCUDPServer(("127.0.0.1", SERVER_PORT), dispatcher)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    yield server

    server.shutdown()
    server_thread.join()

@pytest.fixture(scope="module")
def client() -> SimpleUDPClient:
    return SimpleUDPClient("127.0.0.1", CLIENT_PORT)

def query_and_await(client: SimpleUDPClient,
                    server: ThreadingOSCUDPServer,
                    address: str,
                    fn: Callable = None):
    client.send_message(address, [])
    return await_reply(server, address, fn)

def await_reply(server: ThreadingOSCUDPServer, address: str, fn: Callable = None, timeout: float = TICK_DURATION):
    """
    Awaits a reply from the given `address`, and optionally asserts that the function `fn`
    returns True when called with the returned OSC parameters.

    Args:
        server: OSC server
        address: OSC reply address
        fn: Optional assertion function
        timeout: Maximum number of seconds to wait for a successful reply

    Returns:
        True if the reply is received within the timeout period and the assertion succeeds,
        False otherwise

    """
    event = threading.Event()

    def received_response(address: str, *params):
        if fn is None or fn(address, *params):
            nonlocal event
            event.set()
        nonlocal handler
        server.dispatcher.unmap(address, handler)
        #--------------------------------------------------------------------------------
        # handler reference must be cleared for GC to occur, which allows the server
        # to be shutdown cleanly.
        #--------------------------------------------------------------------------------
        handler = None

    handler = server.dispatcher.map(address, received_response)
    event.wait(timeout)
    return event.is_set()

def wait_one_tick():
    """
    Sleep for one Ableton Live tick (100ms).
    """
    time.sleep(TICK_DURATION)
