import inspect
import logging
logger = logging.getLogger("abletonosc")

def describe_module(module):
    """
    Describe the module object passed as argument
    including its root classes and functions """

    logger.info("Module: %s" % module)
    for name in dir(module):
        obj = getattr(module, name)
        if inspect.ismodule(obj):
            describe_module(obj)
        elif inspect.isclass(obj):
            logger.info("Class: %s" % name)
            members = inspect.getmembers(obj)

            logger.info("Builtins")
            for name, member in members:
                if inspect.isbuiltin(member):
                    logger.info(" - %s" % (name))

            logger.info("Functions")
            for name, member in members:
                if inspect.isfunction(member):
                    logger.info(" - %s" % (name))

            logger.info("Properties")
            for name, member in members:
                if str(type(member)) == "<type 'property'>":
                    logger.info(" - %s" % (name))

            logger.info("----------")

    for name in dir(module):
        obj = getattr(module, name)
        if inspect.ismethod(obj) or inspect.isfunction(obj):
            logger.info("Method", obj)