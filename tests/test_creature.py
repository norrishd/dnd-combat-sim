import random
from pathlib import Path

import pandas as pd

from dnd_combat_sim.attack import MeleeAttack, RangedAttack
from dnd_combat_sim.creature import Abilities, Creature
from dnd_combat_sim.weapons import scimitar, shortbow


class TestCreature:
    def test_init_creature(self):
        """Test can instantiate an arbitrary creature."""
        # Arrange
        num_hit_die = random.randint(1, 10)
        hit_die = random.choice([6, 8, 10, 12, 20])
        hp = f"{num_hit_die}d{hit_die}"
        cr = random.choice([0, 1 / 8, 1 / 4, 1 / 2] + list(range(1, 31)))

        # Act
        creature = Creature(
            name="Test Creature",
            ac=15,
            hp=hp,
            abilities=[10, 10, 10, 10, 10, 10],
            cr=cr,
            attacks=[scimitar, shortbow],
        )

        # Assert
        assert creature.name == "Test Creature"
        assert creature.ac == 15
        assert num_hit_die * 1 <= creature.max_hp <= num_hit_die * hit_die
        assert creature.hp == creature.max_hp
        assert creature.abilities == Abilities(10, 10, 10, 10, 10, 10)
        assert creature.proficiency == max(cr - 1, 0) // 4 + 2
        assert creature.melee_attacks == [scimitar]
        assert creature.ranged_attacks == [shortbow]

    def test_init_from_template(self):
        """Test can create a creature from a template."""
        options = pd.read_csv(
            Path(__file__).parent.parent / "dnd_combat_sim/monsters.csv", usecols=["name"]
        )
        name = random.choice(options["name"])

        creature = Creature.init(name)
        assert creature.name == name
        assert 2 <= creature.proficiency <= 9
        assert len(creature.melee_attacks) > 0 or len(creature.ranged_attacks) > 0
        assert all(isinstance(attack, MeleeAttack) for attack in creature.melee_attacks)
        assert all(isinstance(attack, RangedAttack) for attack in creature.ranged_attacks)
