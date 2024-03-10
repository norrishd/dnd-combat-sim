"""
# TRAITS
Adhesive (Object Form Only). The mimic adheres to anything that touches it. A Huge or smaller creature adhered to the mimic is also grappled by it (escape DC 13). Ability checks made to escape this grapple have disadvantage.

aggressive. As a bonus action, the orc can move up to its speed toward a hostile creature that it can see.

amphibious (bullywug) - can breathe air and water.

Antimagic Susceptibility. The sword is incapacitated while in the area of an antimagic field. If targeted by dispel magic, the sword must succeed on a Constitution saving throw against the caster's spell save DC or fall unconscious for 1 minute.

Dark Devotion. The cultist has advantage on saving throws against being charmed or frightened.

False Appearance. While the sword remains motionless and isn't flying, it is indistinguishable from a normal sword.
False Appearance (Object Form Only). While the mimic remains motionless, it is indistinguishable from an ordinary object.

Grappler. The mimic has advantage on attack rolls against any creature grappled by it.

hold_breath (lizardfolk) - can hold its breath for 15 minutes.

Keen Sight. The hippogriff has advantage on Wisdom (Perception) checks that rely on sight.

Keen Smell. The rat has advantage on Wisdom (Perception) checks that rely on smell.

Martial advantage: Once per turn, the hobgoblin can deal an extra 7 (2d6) damage to a creature it hits with a weapon attack if that creature is within 5 feet of an ally of the hobgoblin that isn’t incapacitated.

Nimble Escape. The goblin can take the Disengage or Hide action as a bonus action on each of its turns.

Pack Tactics (kobold). The kobold has advantage on an attack roll against a creature if at least one of the kobold's allies is within 5 feet of the creature and the ally isn't incapacitated.

Rampage (gnoll) - When reduces a creature to 0 hit points with a melee attack on its turn, can take a bonus action to move up to half its speed and make a bite attack.

Shapechanger. The mimic can use its action to polymorph into an object or back into its true, amorphous form. Its statistics are the same in each form. Any equipment it is wearing or carrying isn't transformed. It reverts to its true form if it dies.

Standing Leap (bullywug) - can long jump up to 20 feet and high jump up to 10 feet, with or without a running start.

Sunlight Sensitivity (kobold). While in sunlight, the kobold has disadvantage on attack rolls, as well as on Wisdom (Perception) checks that rely on sight.

Swamp Camouflage (bullywug). advantage on Dexterity (Stealth) checks made to hide in swampy terrain.
"""

import logging
from typing import Any, Optional

from dnd_combat_sim.attack import AttackDamage, DamageOutcome
from dnd_combat_sim.conditions import Condition
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.dice import roll
from dnd_combat_sim.rules import Ability, DamageType
from dnd_combat_sim.trait import Battle, OnRollAttackTrait, OnRollDamageTrait, OnTakeDamageTrait

logger = logging.getLogger(__name__)


def get_distance(creature1: Creature, creature2: Creature) -> float:
    """Calculate the distance between two creatures."""
    return ((creature1.x - creature2.x) ** 2 + (creature1.y - creature2.y) ** 2) ** 0.5


### Traits ###
class MartialAdvantage(OnRollDamageTrait):
    """Once per turn, can deal an extra 7 (2d6) damage to a creature hit with a weapon attack if
    that creature is within 5 feet of a non-incapacitated ally."""

    def __init__(self) -> None:
        self.last_used: Optional[int] = None

    def on_roll_damage(
        self, creature: Creature, damage_roll: AttackDamage, battle: Battle
    ) -> dict[str, Any]:
        if self.last_used == battle.round:
            return damage_roll

        allies = battle.get_allies(creature)
        for ally in allies:
            if Condition.incapacitated not in ally.conditions:
                damage_type = list(damage_roll.damages.keys())[0]
                extra_damage = roll("2d6")
                logger.debug(
                    f"{creature.name} used martial advantage to roll an extra {extra_damage} "
                    f"{damage_type} damage."
                )
                damage_roll.damages[damage_type] += extra_damage
                self.last_used = battle.round
                break

        return damage_roll


class PackTactics(OnRollAttackTrait):
    """Gets advantage on attack roll if a non-incapacitated ally is within 5 ft of target."""

    def __init__(self) -> None:
        super().__init__()

    def on_roll_attack(
        self, creature: Creature, target: Creature, battle: Battle
    ) -> dict[str, Any]:
        for ally in battle.get_allies(creature):
            if Condition.incapacitated not in ally.conditions and get_distance(ally, target) <= 5:
                logger.debug(f"{creature.name} attacks with advantage thanks to pack tactics!")
                return {"advantage": True}


class UndeadFortitude(OnTakeDamageTrait):
    """Trait for zombies."""

    def on_take_damage(
        self,
        creature: Creature,
        damage: AttackDamage,
        damage_result: DamageOutcome,
    ) -> None:
        """If damage reduces the zombie to 0 hit points, it must make a Constitution saving throw
        with a DC of 5 + the damage taken, unless the damage is radiant or from a critical hit. On a
        success, the zombie drops to 1 hit point instead.
        """
        if damage_result not in {DamageOutcome.knocked_out, DamageOutcome.dead}:
            return damage_result

        if damage.from_crit:
            logger.debug("Undead fortitude overcome by crit")
            return damage_result
        if DamageType.radiant in damage.damages:
            logger.debug("Undead fortitude overcome by radiant damage")
            return damage_result

        save = creature.roll_saving_throw(Ability.con)
        dc = 5 + damage.total
        if save >= dc:
            creature.heal(1)
            logger.debug(
                f"{creature.name} passed DC {dc} undead fortitude const save with a {save} and "
                "reanimated! "
            )
            return DamageOutcome.reanimated

        logger.debug(f"{creature.name} failed DC {dc} undead fortitude const save with a {save}.")
        return damage_result


TRAITS = {
    "pack_tactics": PackTactics,
    "undead_fortitude": UndeadFortitude,
}


def attach_traits(creature: Creature) -> None:
    """Helper function to instantiated and attach traits to creatures.

    To avoid circular import of traits.py <-> creature.py, must attach outside of creature.py.
    """
    instantiated_traits = []
    for trait_name, trait in TRAITS.items():
        if trait_name in creature.traits:
            instantiated_traits.append(trait())

    creature.traits = instantiated_traits
