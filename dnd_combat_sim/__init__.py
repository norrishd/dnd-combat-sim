import logging

from .attack import Attack, DamageType, MeleeAttack, RangedAttack
from .creature import Creature
from .encounter import Encounter1v1

logging.basicConfig(format="", level=logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.WARNING)
