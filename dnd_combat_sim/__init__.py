import logging

logging.basicConfig(format="", level=logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.WARNING)
