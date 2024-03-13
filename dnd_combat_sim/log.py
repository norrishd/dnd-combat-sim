import logging
import time
from typing import Union
from dnd_combat_sim.conditions import TempCondition

from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import DamageOutcome
from dnd_combat_sim.traits.weapon_traits import WeaponTrait
from dnd_combat_sim.weapon import AttackDamage, AttackRoll, Weapon

logger = logging.getLogger(__name__)


class EncounterLogger:
    """Class to log details of an encounter."""

    def log_encounter(self, i):
        self._log_and_pause(f"\n\n*** Encounter {i + 1} ***", level=25)

    def log_roll_initiative(self, initiative: dict[Creature, int]):
        init_str: str = "\n".join(
            f"{creature}: rolled {initiative}" for creature, initiative in initiative.items()
        )
        self._log_and_pause(f"Initiative:\n{init_str}", level=25)

    def log_start_round(self, round_number: int):
        self._log_and_pause(f"\n* Round {round_number} *")

    def log_choose_action(self, creature: Creature, action: str):
        self._log_and_pause(f"{creature.name} takes the {action} action. TODO implement")

    def log_attack_modifiers(
        self,
        weapon_modifiers,
        attacker_trait_modifiers,
        attacker_condition_modifiers,
        target_condition_modifiers,
    ):
        msg = ""
        if weapon_modifiers:
            msg += f"Weapon trait: {weapon_modifiers}\n"
        if attacker_trait_modifiers:
            msg += f"Attacker traits: {attacker_trait_modifiers}"
        if attacker_condition_modifiers:
            msg += f"Attacker conditions: {attacker_condition_modifiers}"
        if target_condition_modifiers:
            msg += f"Target conditions: {target_condition_modifiers}"

        if msg:
            self._log_and_pause(msg)

    def log_miss(self, attacker: Creature, target: Creature, attack_roll: AttackRoll):
        msg = (
            f"{attacker.name} attacks {target.name} with {attack_roll.weapon.name}: rolls "
            f"{attack_roll}: misses"
        )
        self._log_and_pause(msg)

    def log_hit(
        self,
        attacker: Creature,
        target: Creature,
        attack_roll: AttackRoll,
        attack_damage: AttackDamage,
        modified_damage: AttackDamage,
        attack_traits_applied: list[WeaponTrait],
        damage_taken: AttackDamage,
        damage_result: DamageOutcome,
    ):
        if damage_result == DamageOutcome.still_dying:
            msg = (
                f"{attacker.name} attacks {target.name} while down with {attack_roll.weapon.name}: "
            )
            if attack_damage.crit:
                msg += "CRITS for 2 automatic death saving throws"
            else:
                msg += "hits for an automatic death saving throw"
            return self._log_and_pause(f"{target.name} is on death's door")

        msg = (
            f"{attacker.name} attacks {target.name} with {attack_roll.weapon.name}: "
            f"rolls {attack_roll}: {'CRITS' if attack_roll.is_crit else 'hits'} for "
            f"{modified_damage} damage"
        )
        if attack_damage.total != damage_taken.total:
            msg += f" (modified from {attack_damage} by {attack_traits_applied})"

        self._log_and_pause(msg)
        if damage_result == DamageOutcome.knocked_out:
            self._log_and_pause(f"{target.name} is down!")
        elif damage_result in {DamageOutcome.dead, DamageOutcome.instant_death}:
            self._log_and_pause(f"{target.name} is DEAD!")

    def log_weapon_effects(self, weapon_effects: list[TempCondition]):
        if weapon_effects:
            self._log_and_pause(f"New condition: {weapon_effects}")

    def log_end_round(self, creatures: list[Creature]):
        self._log_and_pause(creatures)

    def log_winner(self, winner: Creature):
        self._log_and_pause(f"Winner: {winner}", level=25)

    def _log_and_pause(self, message: str, level=logging.INFO):
        logger.log(level, message)
        # time.sleep(sleep_time)
