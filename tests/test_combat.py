import pytest

from dnd_combat_sim.attacks import MeleeAttack
from dnd_combat_sim.creature import Creature, Stats
from dnd_combat_sim.game import Encounter1v1


@pytest.fixture
def orc():
    return Creature(
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


@pytest.fixture
def hobgoblin():
    return Creature(
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
