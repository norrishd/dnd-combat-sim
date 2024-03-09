from dnd_combat_sim.attack import MeleeAttack
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.utils import parse_stats
from dnd_combat_sim.weapons import (
    bite,
    bite_small,
    dagger,
    heavy_club,
    javelin,
    longbow,
    sling,
    spear,
)

bullywug = Creature(
    "Bullywug",
    stats=parse_stats(15, "2d8", [12, 12, 13, 7, 10, 7], speed=20),
    melee_attacks=[MeleeAttack("Bite", "1d4 bludgeoning"), spear],
    attacks_per_action=2,
    spare_hand=False,
)

gnoll = Creature(
    "Gnoll",
    stats=parse_stats(15, "5d8", [14, 12, 11, 6, 10, 7]),
    melee_attacks=[bite_small, spear, longbow],
    spare_hand=False,
)

kobold = Creature(
    "Kobold",
    stats=parse_stats(12, "2d6", [7, 15, 9, 8, 7, 8]),
    melee_attacks=[dagger],
    ranged_attacks=[sling],
)

spiked_shield = MeleeAttack("Spiked Shield", damage="1d6 piercing")
lizardfolk = Creature(
    "Lizardfolk",
    stats=parse_stats(15, "4d8", [15, 10, 13, 7, 12, 7]),
    melee_attacks=[bite, heavy_club, javelin, spiked_shield],
    attacks_per_action=2,
    spare_hand=False,
)
