import logging
from dnd_combat_sim.conditions import TempCondition

from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import Condition, DamageOutcome, Position
from dnd_combat_sim.traits.weapon_traits import WeaponTrait
from dnd_combat_sim.utils import get_distance
from dnd_combat_sim.weapon import AttackDamage, AttackRoll

logger = logging.getLogger(__name__)

logging.basicConfig(format="%(message)s", level=logging.INFO)
logging.getLogger("asyncio").setLevel(logging.WARNING)


class EncounterLogger:
    """Class to log details of an encounter."""

    def log_encounter(self, i):
        self._log_and_pause(f"\n\n*** Encounter {i + 1} ***", level=25)

    def log_roll_initiative(self, initiative: dict[Creature, int]):
        init_str: str = "\n".join(
            f"{creature}: rolled {initiative=}" for creature, initiative in initiative.items()
        )
        self._log_and_pause(f"Roll initiative:\n{init_str}", level=25)

    def log_start_round(self, round_number: int):
        self._log_and_pause(f"\n* Round {round_number} *")

    def log_choose_action(self, creature: Creature, action: str):
        self._log_and_pause(f"{creature.name} takes the {action} action. TODO implement")

    def log_movement(
        self,
        attacker: Creature,
        target: Creature,
        new_position: Position,
        distance: float,
        dash: bool = False,
    ):
        movement = "dashes" if dash else "moves"
        direction = "towards" if distance > 0 else "away from"
        new_distance = get_distance(new_position, target.position)
        self._log_and_pause(
            f"{attacker.name} {movement} {int(abs(distance))} ft {direction} {target.name} from "
            f"{attacker.position} -> {new_position}: {int(new_distance)} ft apart"
        )

    def log_attack_modifiers(
        self,
        position_modifiers,
        weapon_modifiers,
        attacker_trait_modifiers,
        attacker_condition_modifiers,
        target_condition_modifiers,
    ):
        msg = ""
        span = ""
        if position_modifiers:
            msg += f"Position modifiers: {position_modifiers}"
            span = "\n"
        if weapon_modifiers:
            msg += f"{span}Weapon trait: {weapon_modifiers}"
            span = "\n"
        if attacker_trait_modifiers:
            msg += f"{span}Attacker traits: {attacker_trait_modifiers}"
            span = "\n"
        if attacker_condition_modifiers:
            msg += f"{span}Attacker conditions: {attacker_condition_modifiers}"
            span = "\n"
        if target_condition_modifiers:
            msg += f"{span}Target conditions: {target_condition_modifiers}"

        if msg:
            self._log_and_pause(msg, level=logging.DEBUG)

    def cache_attack(
        self,
        attacker: Creature,
        target: Creature,
        thrown: bool,
        modifiers: dict[str, bool],
        attack_roll: AttackRoll,
    ):
        span = " while down" if Condition.dying in target.conditions else ""
        if thrown:
            msg = f"{attacker.name} throws {attack_roll.weapon.name} at {target.name}{span}"
        else:
            msg = f"{attacker.name} attacks {target.name}{span} with {attack_roll.weapon.name}"

        advantage_cause = None
        disadvantage_cause = None
        # if modifiers:
        #     breakpoint()
        for modifier, cause in modifiers.items():
            if modifier == "advantage":
                advantage_cause = cause.replace("_", " ")
            elif modifier == "disadvantage":
                disadvantage_cause = cause.replace("_", " ")
        if advantage_cause and not disadvantage_cause:
            msg += f" with advantage ({advantage_cause})"
        elif disadvantage_cause and not advantage_cause:
            msg += f" with disadvantage ({disadvantage_cause})"

        self.attack_str = msg

    def log_miss(self, attack_roll: AttackRoll):
        self._log_and_pause(f"{self.attack_str}: rolls {attack_roll}: misses")
        self.attack_str = None

    def log_hit(
        self,
        target: Creature,
        attack_roll: AttackRoll,
        attack_damage: AttackDamage,
        attack_traits_applied: list[WeaponTrait],
        resistances: dict[str, float],
        damage_taken: AttackDamage,
        damage_outcome: DamageOutcome,
    ):
        if damage_outcome == DamageOutcome.still_dying:
            if attack_damage.crit:
                msg = "CRITS for 2 automatic death saving throws: "
            else:
                msg = "hits for an automatic death saving throw: "
            return self._log_and_pause(
                f"{self.attack_str}: {msg}. {target.name} is on death's door"
            )

        msg = (
            f"{self.attack_str}: rolls {attack_roll}: {'CRITS' if attack_roll.is_crit else 'hits'} "
            f"for {damage_taken} damage"
        )
        if attack_traits_applied:
            msg += f" (modified by {attack_traits_applied})"
        if resistances:
            extra = [f"{modifier} to {dtype.name}" for dtype, modifier in resistances.items()]
            extra = ", ".join(extra)
            msg += f" ({extra})"

        self._log_and_pause(msg)

    def log_damage_outcome(self, target: Creature, damage_outcome: DamageOutcome):
        if damage_outcome == DamageOutcome.knocked_out:
            self._log_and_pause(f"{target.name} is down!")
        elif damage_outcome in {DamageOutcome.dead, DamageOutcome.instant_death}:
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
