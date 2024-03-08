from dnd_combat_sim.utils import simple_monster
from dnd_combat_sim.weapons import club, light_crossbow, scimitar

bandit = simple_monster(
    "Bandit",
    ac=12,
    hp="2d8",
    stats=[10, 10, 10, 10, 10, 10],
    melee_attacks=[scimitar],
    ranged_attacks=[light_crossbow],
)

commoner = simple_monster(
    "Commoner",
    ac=10,
    hp="1d8",
    stats=[10, 10, 10, 10, 10, 10],
    melee_attacks=[club],
)

cultist = simple_monster(
    "Cultist",
    ac=12,
    hp="2d8",
    stats=[11, 12, 10, 10, 11, 10],
    melee_attacks=[scimitar],
)
