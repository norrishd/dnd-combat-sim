import logging

# logging.basicConfig(format="%(name)s %(message)s", level=logging.DEBUG)
logging.basicConfig(format="%(message)s", level=logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.WARNING)
