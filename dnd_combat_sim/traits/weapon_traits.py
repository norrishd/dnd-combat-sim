"""Special traits that apply to attacks/weapons, e.g. adhesive, lance, net."""

import abc
import logging
from typing import Optional
from dnd_combat_sim.weapon import Weapon
from dnd_combat_sim.conditions import TempCondition
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import Ability, Condition, Size, Skill
from dnd_combat_sim.traits.trait import Trait
from dnd_combat_sim.utils import get_distance

logger = logging.getLogger(__name__)


##############################
### Abstract attack traits ###
##############################
class WeaponTrait(Trait):
    """Abstract base class for traits that modify a weapon's roll or damage."""


class OnRollAttackWeaponTrait(WeaponTrait):
    """Base class for traits that modify an weapon roll."""

    @abc.abstractmethod
    def on_roll_attack(self, attacker: Creature, target: Creature) -> dict[str, str]:
        """Modify the attack roll, e.g. impose disadvantage on the attack roll.

        Return a reason and a modifier, e.g. "advantage" or "disadvantage"
        """


class OnHitWeaponTrait(WeaponTrait):
    """Base class for traits that do something when an attack hits, e.g. cause a temporary
    condition.
    """

    @abc.abstractmethod
    def on_attack_hit(self, attacker: Creature, target: Creature) -> Optional[TempCondition]:
        """Do something when an attack hits, e.g. cause a temporary condition."""


##############################
### Concrete attack traits ###
##############################
class Adhesive(OnHitWeaponTrait):
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


class Lance(OnRollAttackWeaponTrait):
    """Lance martial weapon. Has disadvantage when attacking within 5ft."""

    def on_roll_attack(self, attacker: Creature, target: Creature) -> dict[str, str]:
        if get_distance(attacker, target) <= 5:
            return {"lance @ 5 ft": "disadvantage"}
        return {}


class Net(OnHitWeaponTrait):
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
