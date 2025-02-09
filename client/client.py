import argparse
import threading
from pythonosc.udp_client import SimpleUDPClient, OscBundle, OscMessageBuilder
from pythonosc.osc_bundle_builder import OscBundleBuilder
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from typing import Callable, Iterable

REMOTE_PORT = 11000
LOCAL_PORT = 11001

#--------------------------------------------------------------------------------
# An Ableton Live tick is 100ms. This constant is typically used for timeouts,
# and factors in some extra time for processing overhead.
#--------------------------------------------------------------------------------
TICK_DURATION = 0.150

class AbletonOSCClient:
    def __init__(self, hostname="127.0.0.1", port=REMOTE_PORT, client_port=LOCAL_PORT):
        """
        Create a client to connect to an Ableton OSC instance.
        Args:
            hostname: The remote host to connect to.
            port: The remote port to connect to. Defaults to 11000, the default AbletonOSC port.
            client_port: The local port to bind to. Defaults to 11001, the default AbletonOSC reply port.
        """
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self.handle_osc)
        self.server = ThreadingOSCUDPServer(("0.0.0.0", client_port), dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.address_handlers = {}
        self.client = SimpleUDPClient(hostname, port)
        self.verbose = False

    def handle_osc(self, address, *params):
        # print("Received OSC: %s %s" % (address, params))
        if address in self.address_handlers:
            self.address_handlers[address](address, params)
        if self.verbose:
            print(address, params)

    def stop(self):
        self.server.shutdown()
        self.server_thread.join()
        self.server = None

    def send_bundle(self,
                    messages: list[tuple[str, tuple]]):

        import time
        now = int(time.time())
        bundle_builder = OscBundleBuilder(now)
        for address, params in messages:
            builder = OscMessageBuilder(address=address)
            for param in params:
                builder.add_arg(param)
            msg = builder.build()
            bundle_builder.add_content(msg)
        bundle = bundle_builder.build()
        self.client.send(bundle)

    def send_message(self,
                     address: str,
                     params: Iterable = ()):
        """
        Send a message to the given OSC address on the server.

        Args:
            address (str): The OSC address to send to (e.g. /live/song/set/tempo)
            params (Iterable): Optional list of arguments to pass to the OSC message.
        """
        self.client.send_message(address, params)

    def set_handler(self,
                    address: str,
                    fn: Callable = None):
        """
        Set the handler for the specified OSC message.

        Args:
            address (str): The OSC address to listen for (e.g. /live/song/get/tempo)
            fn (Callable): The function to trigger when a message received.
                           Must accept a two arguments:
                            - str: the OSC address
                            - tuple: the OSC parameters
        """
        self.address_handlers[address] = fn

    def remove_handler(self,
                       address: str):
        """
        Remove the handler for the specified OSC message.

        Args:
            address (str): The OSC address whose handler to remove.
        """
        del self.address_handlers[address]

    def await_message(self,
                      address: str,
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
        rv = None
        _event = threading.Event()

        def received_response(address, params):
            print("Received response: %s %s" % (address, str(params)))
            nonlocal rv
            nonlocal _event
            rv = params
            _event.set()

        self.set_handler(address, received_response)
        _event.wait(timeout)
        self.remove_handler(address)
        if not _event.is_set():
            raise RuntimeError("No response received to query: %s" % address)
        return rv

    def query(self,
              address: str,
              params: tuple = (),
              timeout: float = TICK_DURATION):
        rv = ()
        _event = threading.Event()
        data_sent_in_chunks = False
        msg_id = 0
        n_chunk_received = 0
        total_chunks = 0

        def received_response(address, params):
            nonlocal rv
            nonlocal _event
            nonlocal data_sent_in_chunks
            nonlocal msg_id
            nonlocal n_chunk_received
            nonlocal total_chunks
            
            rv += tuple(params)

            delimiter = '#$#'
            # If response data was sent in chunks due to socket size limit,
            # the last 4 pieces of information of a chunk are
            # chunk index, total chunks, message id, '#$#'
            
            if params and params[-1] == delimiter:
                data_sent_in_chunks = True
                msg_id = params[-2]
                total_chunks = params[-3]
                chunk_id = params[-4]
                n_chunk_received += 1

            # Assuming that consecutive chunks received within the timeout have the same message ID
            # TODO: Handle chunks with different message IDs
            if not data_sent_in_chunks or (n_chunk_received == total_chunks):
                _event.set()

        self.set_handler(address, received_response)
        self.send_message(address, params)
        _event.wait(timeout)
        self.remove_handler(address)
        if not _event.is_set():
            if data_sent_in_chunks:
                print(f"Timeout! Recevied {n_chunk_received} / {total_chunks} chunks.") 
                print("Try lowering max_chunk_size in send() in osc_server.py if problem persists")
            raise RuntimeError("No response received to query: %s" % address)
        return rv

def main(args):
    client = AbletonOSCClient(args.hostname, args.port)
    client.send_message("/live/song/set/tempo", [125.0])
    tempo = client.query("/live/song/get/tempo")
    print("Got song tempo: %.1f" % tempo[0])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client for AbletonOSC")
    parser.add_argument("--hostname", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=str, default=11000)
    args = parser.parse_args()
    main(args)
