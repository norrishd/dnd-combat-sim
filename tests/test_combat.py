import pytest

from dnd_combat_sim.attack import MeleeAttack
from dnd_combat_sim.creature import Creature, Stats
from dnd_combat_sim.encounter import Encounter1v1


def test_can_deal_damage(orc, hobgoblin):
    """Test a creature can deal damage, assuming the attack hit."""
    orc_starting_hp = orc.stats.hp

    hobgoblin_damage = hobgoblin.roll_damage(hobgoblin.melee_attacks[0])
    orc.take_damage(hobgoblin_damage)

    assert 2 <= hobgoblin_damage <= 9  # 1d8 + 1
    assert orc.stats.hp == max(0, orc_starting_hp - hobgoblin_damage)


def test_1v1(orc, hobgoblin):
    """Test a simple 1v1 combat."""
    encounter = Encounter1v1(orc, hobgoblin)
    encounter.run(to_the_death=True)
