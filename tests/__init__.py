import time
import pytest

from ..client import AbletonOSCClient, TICK_DURATION

# Live tick is 100ms. Wait for this long plus a short additional buffer.
TICK_DURATION = 0.125

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
