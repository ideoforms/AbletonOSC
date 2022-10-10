from . import client, server, query_and_await, await_reply, wait_one_tick

#--------------------------------------------------------------------------------
# Test generic application features
#--------------------------------------------------------------------------------

def test_application_get_version(client, server):
    assert query_and_await(client, server, "/live/application/get/version", (),
                           lambda *params: len(params) == 2 and params[0] == 11)

def test_application_test(client, server):
    assert query_and_await(client, server, "/live/test", ())
