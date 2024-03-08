from dnd_combat_sim.attack import MeleeAttack
from dnd_combat_sim.utils import simple_monster
from dnd_combat_sim.weapons import shortbow, shortsword

skeleton = simple_monster("Skeleton", 13, "2d8", [10, 14, 15, 6, 8, 5], [shortsword], [shortbow])
zombie = simple_monster(
    "Zombie", 8, "3d8", [13, 6, 16, 3, 6, 5], [MeleeAttack("Slam", "1d6 bludgeoning")]
)
