from dnd_combat_sim.attack import MeleeAttack
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.utils import parse_stats
from dnd_combat_sim.weapons import beak_large, bite_big, claws

hippogriff = Creature(
    "Hippogriff",
    stats=parse_stats(11, "3d10", [17, 13, 13, 2, 12, 8], 40),
    melee_attacks=[beak_large, claws],
    attacks_per_action=2,
)

mimic = Creature(
    "Mimic",
    stats=parse_stats(12, "9d8", [17, 12, 15, 5, 13, 8]),
    melee_attacks=[
        MeleeAttack("Pseudopod", damage="1d8 bludgeoning", bonus_damage="1d8 acid"),
        bite_big,
    ],
)
