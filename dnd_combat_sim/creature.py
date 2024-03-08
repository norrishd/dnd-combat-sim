from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Collection, Optional

from .attacks import Attack, unarmed_strike
from .dice import roll, roll_d20


class Ability(StrEnum):
    """Character abilities."""

    strength = auto()
    dexterity = auto()
    constitution = auto()
    intelligence = auto()
    wisdom = auto()
    charisma = auto()


class Condition(StrEnum):
    """Possible conditions."""

    blinded = auto()
    charmed = auto()
    deafened = auto()
    frightened = auto()
    grappled = auto()
    incapacitated = auto()
    invisible = auto()
    paralyzed = auto()
    petrified = auto()
    poisoned = auto()
    prone = auto()
    restrained = auto()
    stunned = auto()
    unconscious = auto()
    dying = auto()
    dead = auto()


class Skill(StrEnum):
    """Character skills."""

    acrobatics = auto()
    animal_handling = auto()
    arcana = auto()
    athletics = auto()
    deception = auto()
    history = auto()
    insight = auto()
    intimidation = auto()
    investigation = auto()
    medicine = auto()
    nature = auto()
    perception = auto()
    performance = auto()
    persuasion = auto()
    religion = auto()
    sleight_of_hand = auto()
    stealth = auto()
    survival = auto()


@dataclass
class Stats:
    """Statistics for a creature."""

    ac: int
    # TODO include size/infer from hit die or vice versa?
    hit_die: int = 8
    level: int = 2
    speed: int = 30
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    use_average_hp: bool = False

    def __post_init__(self):
        if self.use_average_hp:
            self.max_hp = int(
                (roll(self.hit_die, use_average=True) + self.get_modifier(Ability.constitution))
                * self.level
            )
        else:
            self.max_hp = sum(
                roll(self.hit_die, use_average=False) + self.get_modifier(Ability.constitution)
                for _ in range(self.level)
            )
        self.hp = self.max_hp

    def get_modifier(self, ability: Ability) -> int:
        """Get the modifier for an ability score."""
        score = getattr(self, ability.name)
        return (score - 10) // 2


class Creature:
    """Class to store all state for a creature."""

    def __init__(
        self,
        name: str,
        stats: Stats,
        skill_proficiencies: Optional[Collection[Skill]] = None,
        melee_attacks: list[Attack] = None,
        ranged_attacks: list[Attack] = None,
        # spell_slots: dict[str, int] = None,
        # spells: list[Spell] = None,
        make_death_saves: bool = False,
    ) -> None:
        """Create a creature."""
        self.name = name
        self.stats = stats
        self.melee_attacks = melee_attacks
        self.melee_attacks.append(unarmed_strike)
        self.ranged_attacks = ranged_attacks
        # self.total_spell_slots = spell_slots
        # self.spell_slots = spell_slots.copy() if spell_slots is not None else None
        self.conditions = set()
        self.death_saves = {"successes": 0, "failures": 0}
        self.make_death_saves = make_death_saves

    def __repr__(self) -> str:
        return f"{self.name} ({self.stats.hp}/{self.stats.max_hp})"

    def choose_action(self) -> tuple[str, Optional[str]]:
        """Choose an action and bonus action for the turn."""
        if self.stats.hp == 0:
            action = "death_saving_throw"
            bonus_action = None
        else:
            action = random.choice(["attack"])
            bonus_action = random.choice([None])  # TODO implement

        return action, bonus_action

    def choose_attack(self) -> Attack:
        """Choose an attack to use against a target."""
        return random.choice(self.melee_attacks)

    def heal(self, amount: int) -> None:
        self.hp = min(self.hp + amount, self.stats.max_hp)

    def roll_attack(self, attack: Attack) -> tuple[int, int, int, bool]:
        """Make an attack roll.

        Return a tuple of (attack total, d20 roll, modifiers, whether is a crit)
        """
        # Roll to attack
        attack_roll = roll_d20()

        ability_mod = self._get_attack_modifier(attack)
        proficiency_bonus = self._get_proficiency() if attack.proficient else 0

        total = attack_roll + ability_mod + proficiency_bonus

        return (total, attack_roll, ability_mod + proficiency_bonus, self._is_crit(attack_roll))

    def roll_damage(self, attack: Attack, melee: bool = True, crit: bool = False) -> int:
        """Roll damage for an attack that has hit."""
        num_dice = attack.damage.num_dice
        if crit:
            num_dice *= 2

        dice_damage = sum(roll(attack.damage.die_size) for _ in range(num_dice))
        str_damage = self.stats.get_modifier(Ability.strength)
        dex_damage = self.stats.get_modifier(Ability.dexterity)

        if melee:
            modifier_damage = max(str_damage, dex_damage) if attack.finesse else str_damage
        else:
            modifier_damage = dex_damage

        return dice_damage + modifier_damage

    def roll_death_save(self) -> tuple[int, str, dict[str, int]]:
        """Roll a death saving throw.

        Return the roll, result, and tally of death saves/failures."""
        roll = roll_d20()

        if roll == 20:
            result = "critical success"
            self.hp = 1
            self._reset_death_saves(wake_up=True)
        else:
            if 10 <= roll <= 19:
                result = "success"
                self.death_saves["successes"] += 1
                if self.death_saves["successes"] == 3:
                    result = "stabilised"
                    self._reset_death_saves(wake_up=False)
            elif 2 <= roll <= 9:
                result = "failure"
                self.death_saves["failures"] += 1
            elif roll == 1:
                result = "critical failure"
                self.death_saves["failures"] += 2

            if self.death_saves["failures"] == 3:
                result = "death"
                self.conditions.discard(Condition.dying)
                self.conditions.discard(Condition.unconscious)
                self.conditions.add(Condition.dead)

        return roll, result, self.death_saves

    def roll_initiative(self):
        return roll_d20() + self.stats.get_modifier(Ability.dexterity)

    def take_damage(self, damage: int, crit: bool = False) -> str:
        """Take damage from a hit and return a string indicating the outcome:

        1. alive: take the damage and stay up.
        2. knocked out: take enough damage to get knocked out, when `self.make_death_saves == True`.
        3. dying: take 1 or 2 automatic failed death saving throws (if already unconsious), but
            still not yet dead.
        3. dead: take enough damage to die, either because:
            - `self.make_death_saves == False`
            - excess damage was at least 2x max HP
            - brought creature to 3+ failed death saving throws
        """
        damage_taken = min(damage, self.stats.hp)
        excess_damage = damage - damage_taken

        # Check for instant death
        if excess_damage > self.stats.max_hp:
            return self._die()

        # Take some damage, possibly get knocked out or killed
        if self.stats.hp > 0:
            self.stats.hp -= damage_taken
            if self.stats.hp == 0:
                if self.make_death_saves:
                    self.conditions.update([Condition.unconscious, Condition.dying])
                    return "knocked out"
                else:
                    return self._die()
        else:
            # Already making death saving throws, get failure(s) instead of damage
            self.death_saves["failures"] += 1 if not crit else 2
            if self.death_saves["failures"] >= 3:
                return self._die()
            return "dying"

        return "alive"

    # Private methods
    def _die(self) -> str:
        self.conditions.add(Condition.dead)
        self.conditions.discard(Condition.dying)
        self.conditions.discard(Condition.unconscious)

        return "dead"

    def _get_attack_modifier(self, attack: Attack) -> int:
        """Get an attack modifier:

        - strength for melee attacks
          - or dexterity for finesse weapons (whichever is higher)
        - dexterity for ranged attacks
          - or strength for thrown weapons, or either for thrown finesse weapons
        """
        str_modifier = self.stats.get_modifier(Ability.strength)
        dex_modifier = self.stats.get_modifier(Ability.dexterity)
        if not attack.finesse:
            return str_modifier

        return max(str_modifier, dex_modifier)

    def _get_proficiency(self) -> int:
        return (self.stats.level - 1) // 4 + 2

    def _is_crit(self, roll: int):
        return roll == 20

    def _reset_death_saves(self, wake_up: bool = False):
        self.death_saves = {"successes": 0, "failures": 0}
        self.conditions.discard(Condition.dying)
        if wake_up:
            self.conditions.discard(Condition.unconscious)
