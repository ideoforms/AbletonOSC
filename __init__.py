from .manager import Manager

def create_instance(c_instance):
    return Manager(c_instance)