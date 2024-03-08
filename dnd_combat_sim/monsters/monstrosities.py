from dnd_combat_sim.attack import MeleeAttack
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.utils import parse_stats

bite = MeleeAttack(
    "Bite",
    damage="1d8 piercing",
)

mimic = Creature(
    "Mimic",
    stats=parse_stats(12, "9d8", [17, 12, 15, 5, 13, 8]),
    melee_attacks=[MeleeAttack("Pseudopod", damage="1d8 bludgeoning", bonus_damage="1d8 acid")],
)
