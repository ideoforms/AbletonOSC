from . import client, wait_one_tick, TICK_DURATION
import pytest

#--------------------------------------------------------------------------------
# Device Variations tests (Live 12+)
#
# To test variations:
# 1. Create an Instrument Rack or Effect Rack on track 0
# 2. Add at least 2 macro variations to the rack
# 3. Run: pytest tests/test_device.py
#
# Note: These tests will be skipped if the device doesn't support variations
# (e.g., not a RackDevice or Live version < 12)
#--------------------------------------------------------------------------------

# Test configuration: Adjust these if your test rack is on a different track/device
RACK_TRACK_ID = 0
RACK_DEVICE_ID = 0

def _device_has_variations(client, track_id, device_id):
    """
    Check if a device supports variations by querying variation_count.
    Returns True if the device is a RackDevice with variation support.
    """
    try:
        result = client.query("/live/device/get/variation_count", (track_id, device_id))
        # If we get a valid response with a variation count, the device supports variations
        return result and len(result) >= 3
    except:
        return False

@pytest.fixture(scope="module", autouse=True)
def _check_rack_device(client):
    """
    Check if a rack device with variations exists on the test track.
    Skip all tests if not found.
    """
    if not _device_has_variations(client, RACK_TRACK_ID, RACK_DEVICE_ID):
        pytest.skip(
            f"No RackDevice with variations found on track {RACK_TRACK_ID}, device {RACK_DEVICE_ID}. "
            "Please create an Instrument Rack or Effect Rack with at least 2 variations to run these tests."
        )

#--------------------------------------------------------------------------------
# Test Device Variations - Read-only properties
#--------------------------------------------------------------------------------

def test_device_variation_count(client):
    """Test that we can read the number of variations."""
    result = client.query("/live/device/get/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))
    assert len(result) == 3
    assert result[0] == RACK_TRACK_ID
    assert result[1] == RACK_DEVICE_ID
    assert isinstance(result[2], int)
    assert result[2] >= 0  # Should have at least 0 variations

def test_device_variation_count_listener(client):
    """Test that we can listen to variation count changes."""
    # Start listening
    client.send_message("/live/device/start_listen/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))
    wait_one_tick()

    # Stop listening
    client.send_message("/live/device/stop_listen/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))
    wait_one_tick()

#--------------------------------------------------------------------------------
# Test Device Variations - Read/write properties
#--------------------------------------------------------------------------------

def test_device_selected_variation_index_get(client):
    """Test that we can read the selected variation index."""
    result = client.query("/live/device/get/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID))
    assert len(result) == 3
    assert result[0] == RACK_TRACK_ID
    assert result[1] == RACK_DEVICE_ID
    assert isinstance(result[2], int)
    # -1 means no variation selected, or 0+ for a selected variation

def test_device_selected_variation_index_set(client):
    """Test that we can set the selected variation index."""
    # Get the current variation and variation count
    current_result = client.query("/live/device/get/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID))
    current_variation = current_result[2]

    count_result = client.query("/live/device/get/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))
    variation_count = count_result[2]

    if variation_count > 0:
        # Try to select the first variation
        client.send_message("/live/device/set/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID, 0))
        wait_one_tick()

        # Verify the change
        result = client.query("/live/device/get/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID))
        assert result[2] == 0

        # Restore original variation
        client.send_message("/live/device/set/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID, current_variation))
        wait_one_tick()
    else:
        pytest.skip("No variations available to test selected_variation_index setter")

def test_device_selected_variation_index_listener(client):
    """Test that we can listen to selected variation changes."""
    # Start listening
    client.send_message("/live/device/start_listen/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID))
    wait_one_tick()

    # Stop listening
    client.send_message("/live/device/stop_listen/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID))
    wait_one_tick()

#--------------------------------------------------------------------------------
# Test Device Variations - Methods
#--------------------------------------------------------------------------------

def test_device_recall_selected_variation(client):
    """Test that we can recall the selected variation."""
    count_result = client.query("/live/device/get/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))
    variation_count = count_result[2]

    if variation_count > 0:
        # Select a variation first
        client.send_message("/live/device/set/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID, 0))
        wait_one_tick()

        # Recall it
        client.send_message("/live/device/recall_selected_variation", (RACK_TRACK_ID, RACK_DEVICE_ID))
        wait_one_tick()
        # No assertion - just verify the command doesn't error
    else:
        pytest.skip("No variations available to test recall_selected_variation")

def test_device_recall_last_used_variation(client):
    """Test that we can recall the last used variation."""
    client.send_message("/live/device/recall_last_used_variation", (RACK_TRACK_ID, RACK_DEVICE_ID))
    wait_one_tick()
    # No assertion - just verify the command doesn't error

def test_device_randomize_macros(client):
    """Test that we can randomize macros."""
    # Store current state by reading selected variation
    current_result = client.query("/live/device/get/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID))
    current_variation = current_result[2]

    # Randomize macros
    client.send_message("/live/device/randomize_macros", (RACK_TRACK_ID, RACK_DEVICE_ID))
    wait_one_tick()

    # Restore to original variation if one was selected
    if current_variation >= 0:
        client.send_message("/live/device/recall_selected_variation", (RACK_TRACK_ID, RACK_DEVICE_ID))
        wait_one_tick()

#--------------------------------------------------------------------------------
# Test Device Variations - Destructive methods (commented out by default)
#--------------------------------------------------------------------------------

# Uncomment these tests if you want to test destructive operations
# WARNING: These will modify your rack's variations!

# def test_device_store_variation(client):
#     """Test that we can store a new variation."""
#     # Get current count
#     count_before = client.query("/live/device/get/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))[2]
#
#     # Store a new variation
#     client.send_message("/live/device/store_variation", (RACK_TRACK_ID, RACK_DEVICE_ID))
#     wait_one_tick()
#
#     # Verify count increased
#     count_after = client.query("/live/device/get/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))[2]
#     assert count_after == count_before + 1
#
#     # Clean up: delete the variation we just created
#     client.send_message("/live/device/set/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID, count_after - 1))
#     wait_one_tick()
#     client.send_message("/live/device/delete_selected_variation", (RACK_TRACK_ID, RACK_DEVICE_ID))
#     wait_one_tick()

# def test_device_delete_selected_variation(client):
#     """Test that we can delete a variation."""
#     # First create a variation to delete
#     client.send_message("/live/device/store_variation", (RACK_TRACK_ID, RACK_DEVICE_ID))
#     wait_one_tick()
#
#     # Get count and select the last variation
#     count_before = client.query("/live/device/get/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))[2]
#     client.send_message("/live/device/set/selected_variation_index", (RACK_TRACK_ID, RACK_DEVICE_ID, count_before - 1))
#     wait_one_tick()
#
#     # Delete it
#     client.send_message("/live/device/delete_selected_variation", (RACK_TRACK_ID, RACK_DEVICE_ID))
#     wait_one_tick()
#
#     # Verify count decreased
#     count_after = client.query("/live/device/get/variation_count", (RACK_TRACK_ID, RACK_DEVICE_ID))[2]
#     assert count_after == count_before - 1
