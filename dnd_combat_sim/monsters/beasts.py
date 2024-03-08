from dnd_combat_sim.attack import MeleeAttack
from dnd_combat_sim.utils import simple_monster

giant_rat = simple_monster(
    "Giant Rat",
    ac=12,
    hp="2d6",
    stats=[7, 15, 11, 2, 10, 4],
    melee_attacks=[MeleeAttack(name="Bite", damage="1d4 piercing", finesse=True)],
)
