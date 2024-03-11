from datetime import datetime

from dnd_combat_sim.conditions import TempCondition
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.encounter import Encounter1v1
from dnd_combat_sim.rules import Condition
from dnd_combat_sim.traits.weapon_traits import Adhesive
from dnd_combat_sim.traits.creature_traits import Grappler


def test_grapple():
    """Test creature and weapon traits.

    Check that a mimic can grapple an ogre by attacking with its pseudopod which has the Adhesive
    trait.

    The mimic should then be able to attack with advantage using its Grappler trait.
    """
    ## Arrange
    ogre = Creature.init("ogre")
    mimic = Creature.init("mimic")

    # This will attach creature and weapon traits
    encounter = Encounter1v1(ogre, mimic)
    pseudopod = [attack for attack in mimic.attacks if attack.name == "pseudopod"][0]
    adhesive = [trait for trait in pseudopod.traits][0]
    # grappler = [trait for trait in mimic.traits if trait.name == "grappler"][0]

    ## Act
    # Pretend mimic attacks with pseudopod and that it hits
    condition = encounter._apply_weapon_hit_traits(pseudopod, mimic, ogre)
    encounter.battle.add_condition(condition)
    # Pretend it's the next turn - the mimic should be able to attack with advantage
    modifiers, _auto_crit = encounter._get_attack_modifiers(pseudopod, mimic, ogre)
    # Assert
    # Check the mimic has the expected Grappler trait
    assert len(mimic.traits) == 1
    assert isinstance(mimic.traits[0], Grappler)
    # Check pseudopod has the expected Adhesive trait
    assert len(pseudopod.traits) == 1
    assert isinstance(pseudopod.traits[0], Adhesive)

    # Check the appropriate grappled temporary condition is returned
    assert isinstance(condition, TempCondition)
    assert condition.condition == Condition.grappled
    assert condition.target == ogre
    assert condition.caused_by == mimic

    # Check the mimic has advantage on its next attack
    assert modifiers == {"advantage": True}
