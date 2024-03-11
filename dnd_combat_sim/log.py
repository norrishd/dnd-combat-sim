import logging
import time
from typing import Union
from dnd_combat_sim.conditions import TempCondition

from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import DamageOutcome
from dnd_combat_sim.weapon import AttackDamage, AttackRoll, Weapon

logger = logging.getLogger(__name__)


class EncounterLogger:
    """Class to log details of an encounter."""

    def __init__(self) -> None:
        self.level = logging.DEBUG

    def log_encounter(self, i):
        self._log_and_pause(f"\n*** Encounter {i + 1} ***", logging.INFO)

    def log_roll_initiative(self, initiative: dict[Creature, int]):
        init_str: str = "\n".join(
            f"{creature}: rolled {initiative}" for creature, initiative in initiative.items()
        )
        self._log_and_pause(f"Initiative:\n{init_str}", logging.INFO)

    def log_start_round(self, round_number: int):
        self._log_and_pause(f"* Round {round_number} *", level=logging.INFO)

    def log_choose_action(self, creature: Creature, action: str):
        self._log_and_pause(
            f"{creature.name} takes the {action} action. TODO implement", logging.INFO
        )

    def log_attack_modifiers(
        self,
        weapon_modifiers,
        attacker_trait_modifiers,
        attacker_condition_modifiers,
        target_condition_modifiers,
    ):
        msg = ""
        if weapon_modifiers:
            msg += f"Weapon modifiers: {weapon_modifiers}\n"
        if attacker_trait_modifiers:
            msg += f"Attacker trait modifiers: {attacker_trait_modifiers}\n"
        if attacker_condition_modifiers:
            msg += f"Attacker condition modifiers: {attacker_condition_modifiers}\n"
        if target_condition_modifiers:
            msg += f"Target condition modifiers: {target_condition_modifiers}\n"

        self._log_and_pause(msg, logging.INFO)

    def log_miss(self, attacker: Creature, target: Creature, attack_roll: AttackRoll):
        msg = (
            f"{attacker.name} attacks {target.name} with {attack_roll.weapon.name}: rolls "
            f" {attack_roll}: miss"
        )
        self._log_and_pause(msg, logging.INFO)

    def log_hit(
        self,
        attacker: Creature,
        target: Creature,
        attack_roll: AttackRoll,
        attack_damage: AttackDamage,
        modified_damage: AttackDamage,
        damage_taken: AttackDamage,
    ):
        msg = f"{attacker.name} attacks {target.name} with {attack_roll.weapon.name}: rolls {attack_roll}: "
        msg += f"{'CRITS' if attack_roll.is_crit else 'hits'} for {modified_damage} damage"
        if attack_damage.total != damage_taken.total:
            msg += f" (modified from {attack_damage})"

    def log_weapon_effects(self, weapon_effects: list[TempCondition]):
        if weapon_effects:
            self._log_and_pause(f"New condition: {weapon_effects}", logging.INFO)

    def log_attack_outcome(self, damage_result: DamageOutcome, target: Creature):
        if damage_result == DamageOutcome.knocked_out:
            self._log_and_pause(f"{target.name} is down!", level=logging.INFO)
        elif damage_result == DamageOutcome.still_dying:
            self._log_and_pause(f"{target.name} is on death's door", level=logging.INFO)
        elif damage_result in {DamageOutcome.dead, DamageOutcome.instant_death}:
            self._log_and_pause(f"{target.name} is DEAD!", level=logging.INFO)

    def log_end_round(self, creatures: list[Creature]):
        self._log_and_pause(creatures, logging.INFO)

    def log_winner(self, winner: Creature):
        self._log_and_pause(f"Winner: {winner}")

    def _log_and_pause(self, message: str, level):
        logger.log(self.level, message)
        # time.sleep(sleep_time)
