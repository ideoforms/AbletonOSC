from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test chain discovery
#--------------------------------------------------------------------------------

def test_device_get_num_chains(client):
    """
    Test getting the number of chains from a rack device.
    Assumes Track 0 has a Drum Rack at device index 0.
    """
    track_id = 0
    rack_device_id = 0

    response = client.query("/live/device/get/num_chains", (track_id, rack_device_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert isinstance(response[2], int)
    assert response[2] >= 1  # At least one chain should exist


def test_chain_get_num_devices(client):
    """
    Test getting the number of devices in a chain.
    Assumes Track 0, Drum Rack at device 0, has at least 1 chain with devices.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0

    response = client.query("/live/chain/get/num_devices", (track_id, rack_device_id, chain_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert isinstance(response[3], int)
    assert response[3] >= 1  # At least one device should exist


#--------------------------------------------------------------------------------
# Test chain device discovery
#--------------------------------------------------------------------------------

def test_chain_device_get_devices_name(client):
    """
    Test getting all device names in a chain.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0

    response = client.query("/live/chain/device/get/devices/name", (track_id, rack_device_id, chain_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id

    # Get number of devices to verify count
    num_devices_response = client.query("/live/chain/get/num_devices", (track_id, rack_device_id, chain_id))
    num_devices = num_devices_response[3]

    # Response should have 3 prefix elements + num_devices device names
    assert len(response) == 3 + num_devices

    # All device names should be strings
    for i in range(3, len(response)):
        assert isinstance(response[i], str)


def test_chain_device_get_devices_type(client):
    """
    Test getting all device types in a chain.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0

    response = client.query("/live/chain/device/get/devices/type", (track_id, rack_device_id, chain_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id

    # Get number of devices to verify count
    num_devices_response = client.query("/live/chain/get/num_devices", (track_id, rack_device_id, chain_id))
    num_devices = num_devices_response[3]

    # Response should have 3 prefix elements + num_devices device types
    assert len(response) == 3 + num_devices

    # All device types should be integers
    for i in range(3, len(response)):
        assert isinstance(response[i], int)


#--------------------------------------------------------------------------------
# Test chain device parameters
#--------------------------------------------------------------------------------

def test_chain_device_get_num_parameters(client):
    """
    Test getting the number of parameters for a device in a chain.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0

    response = client.query("/live/chain/device/get/num_parameters", (track_id, rack_device_id, chain_id, chain_device_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id
    assert isinstance(response[4], int)
    assert response[4] >= 1  # At least one parameter should exist


def test_chain_device_get_parameters_name(client):
    """
    Test getting all parameter names for a device in a chain.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0

    response = client.query("/live/chain/device/get/parameters/name", (track_id, rack_device_id, chain_id, chain_device_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id

    # Get number of parameters to verify count
    num_params_response = client.query("/live/chain/device/get/num_parameters", (track_id, rack_device_id, chain_id, chain_device_id))
    num_params = num_params_response[4]

    # Response should have 4 prefix elements + num_params parameter names
    assert len(response) == 4 + num_params

    # All parameter names should be strings
    for i in range(4, len(response)):
        assert isinstance(response[i], str)


def test_chain_device_get_parameter_value(client):
    """
    Test getting an individual parameter value.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0
    param_id = 1

    response = client.query("/live/chain/device/get/parameter/value", (track_id, rack_device_id, chain_id, chain_device_id, param_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id
    assert response[4] == param_id
    assert isinstance(response[5], (int, float))


def test_chain_device_get_parameter_value_string(client):
    """
    Test getting parameter value as a formatted string.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0
    param_id = 1

    response = client.query("/live/chain/device/get/parameter/value_string", (track_id, rack_device_id, chain_id, chain_device_id, param_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id
    assert response[4] == param_id
    assert isinstance(response[5], str)
    assert len(response[5]) > 0  # String should not be empty


#--------------------------------------------------------------------------------
# Test chain properties
#--------------------------------------------------------------------------------

def test_chain_get_set_name(client):
    """
    Test getting and setting chain name.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0

    # Get original name
    original_response = client.query("/live/chain/get/name", (track_id, rack_device_id, chain_id))
    assert original_response[0] == track_id
    assert original_response[1] == rack_device_id
    assert original_response[2] == chain_id
    original_name = original_response[3]

    # Set new name
    test_name = "TestChain"
    client.send_message("/live/chain/set/name", (track_id, rack_device_id, chain_id, test_name))
    wait_one_tick()

    # Verify new name
    new_response = client.query("/live/chain/get/name", (track_id, rack_device_id, chain_id))
    assert new_response[3] == test_name

    # Restore original name
    client.send_message("/live/chain/set/name", (track_id, rack_device_id, chain_id, original_name))
    wait_one_tick()


def test_chain_get_set_mute(client):
    """
    Test getting and setting chain mute state.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0

    # Get original mute state
    original_response = client.query("/live/chain/get/mute", (track_id, rack_device_id, chain_id))
    original_mute = original_response[3]

    # Toggle mute
    new_mute = 0 if original_mute else 1
    client.send_message("/live/chain/set/mute", (track_id, rack_device_id, chain_id, new_mute))
    wait_one_tick()

    # Verify new state
    new_response = client.query("/live/chain/get/mute", (track_id, rack_device_id, chain_id))
    assert new_response[3] == new_mute

    # Restore original state
    client.send_message("/live/chain/set/mute", (track_id, rack_device_id, chain_id, original_mute))
    wait_one_tick()


def test_chain_get_has_audio_input(client):
    """
    Test getting chain audio input capability.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0

    response = client.query("/live/chain/get/has_audio_input", (track_id, rack_device_id, chain_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert isinstance(response[3], int)


def test_chain_get_color_index(client):
    """
    Test getting chain color index.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0

    response = client.query("/live/chain/get/color_index", (track_id, rack_device_id, chain_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert isinstance(response[3], int)


#--------------------------------------------------------------------------------
# Test individual chain device properties
#--------------------------------------------------------------------------------

def test_chain_device_get_class_name(client):
    """
    Test getting chain device class name.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0

    response = client.query("/live/chain/device/get/class_name", (track_id, rack_device_id, chain_id, chain_device_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id
    assert isinstance(response[4], str)
    assert len(response[4]) > 0


def test_chain_device_get_name(client):
    """
    Test getting chain device name.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0

    response = client.query("/live/chain/device/get/name", (track_id, rack_device_id, chain_id, chain_device_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id
    assert isinstance(response[4], str)
    assert len(response[4]) > 0


def test_chain_device_get_type(client):
    """
    Test getting chain device type.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0

    response = client.query("/live/chain/device/get/type", (track_id, rack_device_id, chain_id, chain_device_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id
    assert isinstance(response[4], int)


#--------------------------------------------------------------------------------
# Test chain device parameter metadata
#--------------------------------------------------------------------------------

def test_chain_device_get_parameters_min_max(client):
    """
    Test getting parameter min and max values.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0

    # Get min values
    min_response = client.query("/live/chain/device/get/parameters/min", (track_id, rack_device_id, chain_id, chain_device_id))
    assert min_response[0] == track_id
    assert min_response[1] == rack_device_id
    assert min_response[2] == chain_id
    assert min_response[3] == chain_device_id

    # Get max values
    max_response = client.query("/live/chain/device/get/parameters/max", (track_id, rack_device_id, chain_id, chain_device_id))
    assert max_response[0] == track_id
    assert max_response[1] == rack_device_id
    assert max_response[2] == chain_id
    assert max_response[3] == chain_device_id

    # Should have same length
    assert len(min_response) == len(max_response)

    # All values should be numeric
    for i in range(4, len(min_response)):
        assert isinstance(min_response[i], (int, float))
        assert isinstance(max_response[i], (int, float))


def test_chain_device_get_parameters_is_quantized(client):
    """
    Test getting parameter quantization status.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0

    response = client.query("/live/chain/device/get/parameters/is_quantized", (track_id, rack_device_id, chain_id, chain_device_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id

    # All values should be integers (booleans as 0/1)
    for i in range(4, len(response)):
        assert isinstance(response[i], int)


def test_chain_device_get_parameter_name(client):
    """
    Test getting individual parameter name.
    """
    track_id = 0
    rack_device_id = 0
    chain_id = 0
    chain_device_id = 0
    param_id = 1

    response = client.query("/live/chain/device/get/parameter/name", (track_id, rack_device_id, chain_id, chain_device_id, param_id))
    assert response[0] == track_id
    assert response[1] == rack_device_id
    assert response[2] == chain_id
    assert response[3] == chain_device_id
    assert response[4] == param_id
    assert isinstance(response[5], str)
    assert len(response[5]) > 0
