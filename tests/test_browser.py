from . import client, wait_one_tick

#--------------------------------------------------------------------------------
# Tests for the Browser API.
#
# These tests rely on devices that ship with every standard Live install:
#   - "Simpler"  (instrument, included since Live Intro)
#   - "Reverb"   (audio effect, included since Live 1)
#
# The lifecycle tests load a device onto a track, verify it shows up in the
# track's device list, mutate parameter 0 (which is always "Device On"
# across every Live device), restore it, and then delete the device, asserting
# that the track returns to its original device count.
#
# Tracks 0 (MIDI) and 2 (Audio) are used to match the convention in the other
# test modules. If a previous test run left devices behind, the autouse
# fixture below clears the test tracks before each test.
#--------------------------------------------------------------------------------

import pytest


def _track_num_devices(client, track_id):
    return client.query("/live/track/get/num_devices", (track_id,))[1]


def _device_param_value(client, track_id, device_id, param_index):
    return client.query("/live/device/get/parameter/value",
                        (track_id, device_id, param_index))[3]


def _purge_track_devices(client, track_id):
    num = _track_num_devices(client, track_id)
    for device_id in reversed(range(num)):
        client.send_message("/live/track/delete_device", (track_id, device_id))
        wait_one_tick()


@pytest.fixture(autouse=True)
def _clean_test_tracks(client):
    """Ensure tracks 0 and 2 have no devices before and after each test."""
    _purge_track_devices(client, 0)
    _purge_track_devices(client, 2)
    yield
    _purge_track_devices(client, 0)
    _purge_track_devices(client, 2)


def _assert_load_modify_delete(client, load_address, device_name, track_id):
    """Run the load -> verify -> mutate -> restore -> delete -> verify cycle."""
    initial_count = _track_num_devices(client, track_id)

    client.send_message(load_address, (device_name, track_id))
    wait_one_tick()

    new_count = _track_num_devices(client, track_id)
    assert new_count == initial_count + 1, \
        "Expected device count to grow by 1 (loading %s onto track %d); got %d -> %d" % \
        (device_name, track_id, initial_count, new_count)

    device_id = new_count - 1
    device_names = client.query("/live/track/get/devices/name", (track_id,))
    loaded_name = device_names[1 + device_id]
    assert device_name.lower() in loaded_name.lower(), \
        "Expected '%s' in loaded device name; got: %s" % (device_name, loaded_name)

    # Parameter 0 is always "Device On" — a 0.0/1.0 toggle that is safe to mutate.
    original_value = _device_param_value(client, track_id, device_id, 0)
    target_value = 0.0 if original_value >= 0.5 else 1.0

    client.send_message("/live/device/set/parameter/value",
                        (track_id, device_id, 0, target_value))
    wait_one_tick()
    assert _device_param_value(client, track_id, device_id, 0) == target_value

    # Restore so we don't leave the test fixture in a surprising state.
    client.send_message("/live/device/set/parameter/value",
                        (track_id, device_id, 0, original_value))
    wait_one_tick()

    client.send_message("/live/track/delete_device", (track_id, device_id))
    wait_one_tick()

    final_count = _track_num_devices(client, track_id)
    assert final_count == initial_count, \
        "Expected device to be removed (count back to %d); got %d" % \
        (initial_count, final_count)


def test_browser_load_instrument_lifecycle(client):
    """Load Simpler onto a MIDI track, mutate a parameter, then delete it."""
    _assert_load_modify_delete(client,
                               load_address="/live/browser/load_instrument",
                               device_name="Simpler",
                               track_id=0)


def test_browser_load_audio_effect_lifecycle(client):
    """Load Reverb onto an audio track, mutate a parameter, then delete it."""
    _assert_load_modify_delete(client,
                               load_address="/live/browser/load_audio_effect",
                               device_name="Reverb",
                               track_id=2)


def test_browser_get_categories(client):
    """Smoke test: /live/browser/get/categories returns a non-empty tuple
    containing at least the always-present core categories."""
    response = client.query("/live/browser/get/categories", ())
    categories = set(response)
    # Every Live install exposes at least these top-level browser roots.
    expected_minimum = {"instruments", "audio_effects", "midi_effects"}
    assert expected_minimum.issubset(categories), \
        "Expected categories to include %s; got %s" % (expected_minimum, categories)
