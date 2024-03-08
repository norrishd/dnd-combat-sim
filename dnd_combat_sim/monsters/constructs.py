from dnd_combat_sim.utils import simple_monster
from dnd_combat_sim.weapons import longsword

flying_sword = simple_monster(
    "Flying Sword",
    ac=17,
    hp="5d6",
    stats=[12, 15, 11, 1, 5, 1],
    melee_attacks=[longsword],
)
