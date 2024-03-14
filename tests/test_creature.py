# pylint: disable=protected-access
import random

from dnd_combat_sim.weapon import Weapon
from dnd_combat_sim.creature import Abilities, Creature
from dnd_combat_sim.rules import Size
from dnd_combat_sim.utils import MONSTERS


class TestCreature:
    def test_init_creature(self):
        """Test can instantiate an arbitrary creature."""
        # Arrange
        num_hit_die = random.randint(1, 10)
        hit_die = random.choice([6, 8, 10, 12, 20])
        hp = f"{num_hit_die}d{hit_die}"
        cr = random.choice([0, 1 / 8, 1 / 4, 1 / 2] + list(range(1, 31)))
        size = random.choice(list(Size.__members__.values()))

        # Act
        creature = Creature(
            name="Test Creature",
            ac=15,
            hp=hp,
            abilities=[10, 11, 12, 13, 14, 16],
            cr=cr,
            attacks=["scimitar", "shortbow"],
            size=size,
        )

        # Assert
        assert creature.name == "Test Creature"
        assert creature.ac == 15
        assert num_hit_die * 1 <= creature.max_hp <= num_hit_die * hit_die
        assert creature.hp == creature.max_hp
        assert creature.abilities == Abilities(10, 11, 12, 13, 14, 16)
        assert creature.proficiency == max(cr - 1, 0) // 4 + 2
        assert creature.weapons == [
            Weapon.init("scimitar", size=size),
            Weapon.init("shortbow", size=size),
        ]

    def test_init_from_template(self):
        """Test can create a creature from a template."""
        options = MONSTERS.index
        name = random.choice(options)

        creature = Creature.init(name)
        assert creature.name == name.title()
        assert 2 <= creature.proficiency <= 9
        assert len(creature.weapons) > 0

    def test_choose_weapon(self):
        """Test cases:

        - Creature in melee, only has melee weapon
        - Creature in melee, only had ranged
        - Creature in melee, has good melee and worse ranged
        - Creature in melee, has poor melee and better ranged (even with disadvantage)


        """
