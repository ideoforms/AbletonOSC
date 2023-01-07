from . import client, wait_one_tick

#--------------------------------------------------------------------------------
# Test generic application features
#--------------------------------------------------------------------------------

def test_application_test(client):
    assert client.query("/live/test")

def test_application_get_version(client):
    rv = client.query("/live/application/get/version")
    assert len(rv) == 2 and rv[0] == 11

def test_application_error(client):
    client.send_message("/live/clip/get/color", (0, 10))
    response = client.await_message("/live/error")
    assert response[0] == "Error handling OSC message: Index out of range"