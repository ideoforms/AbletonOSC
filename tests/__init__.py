import time
import pytest
import threading
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

CLIENT_PORT = 11000
SERVER_PORT = 11001

# Live tick is 100ms. Wait for this long plus a short additional buffer.
TICK_DURATION = 0.11

@pytest.fixture(scope="module")
def server():
    dispatcher = Dispatcher()
    server = ThreadingOSCUDPServer(("127.0.0.1", SERVER_PORT), dispatcher)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    yield server

    server.shutdown()
    server_thread.join()

@pytest.fixture(scope="module")
def client():
    return SimpleUDPClient("127.0.0.1", CLIENT_PORT)

def query_and_await(client, server, address, fn):
    client.send_message(address, [])
    return await_reply(server, address, fn)

def await_reply(server, address, fn, timeout=TICK_DURATION):
    event = threading.Event()
    def received_response(address, *params):
        print("RECEIVED: %s" % str(params))
        if fn(address, *params):
            nonlocal event
            event.set()
    server.dispatcher.map(address, received_response)
    event.wait(timeout)
    return event.is_set()

def wait_one_tick():
    time.sleep(TICK_DURATION)
