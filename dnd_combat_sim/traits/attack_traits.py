"""Special traits that apply to attacks/weapons, e.g. adhesive, lance, net."""

import abc
import logging
from typing import Optional
from dnd_combat_sim.attack import Attack
from dnd_combat_sim.conditions import TempCondition
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import Ability, Condition, Size, Skill
from dnd_combat_sim.traits.trait import Trait
from dnd_combat_sim.utils import get_distance

logger = logging.getLogger(__name__)


##############################
### Abstract attack traits ###
##############################
class AttackTrait(Trait):
    """Abstract base class for traits that modify an attack's roll or damage."""


class OnRollAttackAttackTrait(AttackTrait):
    """Base class for traits that modify an attack roll."""

    @abc.abstractmethod
    def on_roll_attack(self, attacker: Creature, target: Creature) -> dict[str, bool]:
        """Modify the attack roll, e.g. impose disadvantage on the attack roll."""


class OnHitAttackTrait(AttackTrait):
    """Base class for traits that do something when an attack hits, e.g. cause a temporary
    condition.
    """


##############################
### Concrete attack traits ###
##############################
class Adhesive(OnHitAttackTrait):
    """The mimic adheres to anything that touches it. A Huge or smaller creature adhered to the
    mimic is also grappled by it (escape DC 13). Ability checks made to escape this grapple have
    disadvantage.
    """

    def on_attack_hit(self, attacker: Creature, target: Creature) -> Optional[TempCondition]:
        if target.size <= Size.huge:
            return TempCondition(
                Condition.grappled,
                target=target,
                caused_by=attacker,
                escape_dc=13,
                escape_ability=[Skill.acrobatics, Skill.athletics],
                # TODO use these
                escape_modifiers={"disadvantage": True},
                contested_by=[Skill.athletics],
                on_action=True,
            )


class Lance(OnRollAttackAttackTrait):
    """Standard lance martial weapon."""

    def on_roll_attack(self, attacker: Creature, target: Creature) -> dict[str, bool]:
        if get_distance(attacker, target) <= 5:
            return {"disadvantage": True}
        return {}


class Net(OnHitAttackTrait):
    """Standard net martial ranged weapon."""

    def on_attack_hit(self, _attacker: Creature, target: Creature) -> Optional[TempCondition]:
        if target.size <= Size.large:
            # TODO option to destroy by dealing 5 slashing damage to the net (AC 10)
            # TODO handle net preventing multiple attacks
            return TempCondition(
                condition=Condition.restrained,
                target=target,
                escape_dc=10,
                escape_ability=Ability.str,
            )
        return None


ATTACK_TRAITS = {"adhesive": Adhesive, "lance": Lance, "net": Net}


def attach_attack_traits(attack: Attack) -> None:
    """Helper function to instantiated and attach traits to attacks.

    To avoid circular import of traits.py <-> attacks.py, must attach outside of attacks.py.
    """
    instantiated_traits = []
    for trait_name, trait in ATTACK_TRAITS.items():
        if attack.traits is not None and trait_name in attack.traits:
            instantiated_traits.append(trait())

    if attack.traits is not None:
        missing_traits = set(attack.traits) - ATTACK_TRAITS.keys()
        if missing_traits:
            logger.warning("Skipping unimplemented traits")

    attack.traits = instantiated_traits
