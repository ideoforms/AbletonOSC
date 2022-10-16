from . import client, wait_one_tick

#--------------------------------------------------------------------------------
# Test generic application features
#--------------------------------------------------------------------------------

def test_application_test(client):
    assert client.query_and_await("/live/test")

def test_application_get_version(client):
    assert client.query_and_await("/live/application/get/version", (),
                                  lambda params: len(params) == 2 and params[0] == 11)
