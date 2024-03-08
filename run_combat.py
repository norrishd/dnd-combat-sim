from dnd_combat_sim.game import Encounter1v1
from dnd_combat_sim.monsters import *

encounter = Encounter1v1(ogre, mimic)
encounter.run(to_the_death=True)
