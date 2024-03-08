from copy import deepcopy

from dnd_combat_sim.attacks import Damage, DamageType, MeleeAttack, RangedAttack
from dnd_combat_sim.creature import Creature, Stats
from dnd_combat_sim.game import Encounter1v1

orc = Creature(
    "Orc",
    Stats(
        ac=13,
        hit_die=8,
        level=2,
        speed=30,
        strength=16,
        dexterity=12,
        constitution=16,
        intelligence=7,
        wisdom=11,
        charisma=10,
    ),
    melee_attacks=[
        MeleeAttack("Greataxe", hit=5, damage="1d12 slashing"),
        MeleeAttack("Javelin", hit=5, damage="1d6 piercing"),
    ],
)

hobgoblin = Creature(
    "Hobgoblin",
    Stats(
        ac=18,
        hit_die=8,
        level=2,
        speed=30,
        strength=13,
        dexterity=12,
        constitution=12,
        intelligence=10,
        wisdom=10,
        charisma=9,
    ),
    melee_attacks=[MeleeAttack("Longsword", hit=3, damage="1d8 slashing")],
)

encounter = Encounter1v1(orc, hobgoblin)
encounter.run(to_the_death=True)
