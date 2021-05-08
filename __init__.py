try:
    from .manager import Manager
except ImportError as e:
    # This is needed for unit tests to work through pytest.
    # Otherwise, pytest will attempt and fail to import this __init__.py
    exception_str = str(e)
    if "bad magic number" in exception_str:
        pass
    else:
        raise e

def create_instance(c_instance):
    return Manager(c_instance)
