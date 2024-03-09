from __future__ import annotations

import random
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Collection, List, Optional

from .attack import Attack, MeleeAttack, RangedAttack
from .conditions import Condition
from .dice import roll, roll_d20
from .weapons import unarmed_strike


class Ability(StrEnum):
    """Character abilities."""

    strength = auto()
    dexterity = auto()
    constitution = auto()
    intelligence = auto()
    wisdom = auto()
    charisma = auto()


class Size(StrEnum):
    """Creature sizes."""

    tiny = auto()
    small = auto()
    medium = auto()
    large = auto()
    huge = auto()
    gargantuan = auto()


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
    level: int = 2
    hit_die: int = 8  # TODO include size/infer from hit die or vice versa?
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    speed: int = 30
    size: Size = Size.medium

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
        melee_attacks: list[MeleeAttack] = None,
        spare_hand: bool = True,  # If True will use two-handed damage for versatile weapons
        ranged_attacks: list[RangedAttack] = None,
        # spell_slots: dict[str, int] = None,
        # spells: list[Spell] = None,
        attacks_per_action: int = 1,
        multi_attacks_different: bool = True,
        make_death_saves: bool = False,
    ) -> None:
        """Create a creature."""
        self.name = name
        self.stats = stats
        self.melee_attacks = melee_attacks
        self.melee_attacks.append(unarmed_strike)
        self.spare_hand = spare_hand
        self.ranged_attacks = ranged_attacks
        self.attacks_per_action = attacks_per_action
        self.multi_attacks_different = multi_attacks_different
        # self.total_spell_slots = spell_slots or {}
        # self.spell_slots = total_spell_slots.copy() if spell_slots
        self.conditions = set()
        self.death_saves = {"successes": 0, "failures": 0}
        self.make_death_saves = make_death_saves
        self.use_average_hp: bool = False

        # Hit points and temporary hit points
        self.hp = self.max_hp = self._roll_hit_points()
        self.temp_hp: int = 0

    def __repr__(self) -> str:
        return f"{self.name} ({self.hp}/{self.max_hp})"

    def choose_action(self) -> tuple[str, Optional[str]]:
        """Choose an action and bonus action for the turn."""
        if self.hp == 0:
            action = "death_saving_throw"
            bonus_action = None
        else:
            action = random.choice(["attack"])
            bonus_action = random.choice([None])  # TODO implement

        return action, bonus_action

    def choose_attack(self) -> List[Attack]:
        """Choose an attack to use against a target.

        For now, simpply choose the attack with the highest expected damage, not factoring in
        likelihood to hit, advantage/disadvantage, resistances or anything else.
        """
        options = defaultdict(list)
        for attack in self.melee_attacks:
            expected = attack.expected_damage(two_handed=self.spare_hand)
            options[expected].append(attack)

        # Shuffle the order of attacks per damage level
        for expected_damage, attacks in options.items():
            random.shuffle(attacks)
        # Sort from highest expectect damage to lowest
        options = dict(sorted(options.items(), reverse=True))
        best_options = options[list(options.keys())[0]]

        if self.attacks_per_action == 1 or not self.multi_attacks_different:
            # Choose a random attack with equal highest expected damage
            return random.choices(best_options, k=self.attacks_per_action)

        # Multiple attacks and must be different
        sorted_options = []
        for options_set in options.values():
            sorted_options.extend(options_set)
            if len(sorted_options) >= self.attacks_per_action:
                break

        return sorted_options[: self.attacks_per_action]

    def heal(self, amount: int) -> None:
        self.hp = min(self.hp + amount, self.max_hp)

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

    def roll_damage(self, attack: Attack, crit: bool = False) -> int:
        """Roll damage for an attack that has hit."""
        damage = attack._damage
        # Use two-handed damage if have a spare hand
        if attack._two_handed_damage is not None and self.spare_hand:
            damage = attack._two_handed_damage

        num_dice = damage.num_dice if not crit else damage.num_dice * 2
        dice_damage = sum(roll(damage.die_size) for _ in range(num_dice))
        modifier_damage = self._get_attack_modifier(attack)

        bonus_damage = 0
        if attack._bonus_damage is not None:
            # TODO confirm if binus damage can get attack modifiers
            damage = attack._bonus_damage
            num_dice = damage.num_dice if not crit else damage.num_dice * 2
            bonus_damage = sum(roll(attack._bonus_damage) for _ in range(num_dice))

        return max(dice_damage + modifier_damage + bonus_damage, 0)

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

            if self.death_saves["failures"] >= 3:
                result = self._die()

        return roll, result, self.death_saves

    def roll_initiative(self):
        return roll_d20() + self.stats.get_modifier(Ability.dexterity)

    def spawn(self, name: Optional[str] = None) -> Creature:
        new_creature = deepcopy(self)
        if name is not None:
            new_creature.name = name

        # Roll new HP; reset spell slots, conditions and death saves
        new_creature.hp = new_creature.max_hp = self._roll_hit_points()
        # new_creature.spell_slots = self.total_spell_slots.copy()
        new_creature.conditions = set()
        new_creature.death_saves = {"successes": 0, "failures": 0}

        return new_creature

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
        damage_taken = min(damage, self.hp)
        excess_damage = damage - damage_taken

        # Check for instant death
        if excess_damage > self.max_hp:
            return self._die()

        # Take some damage, possibly get knocked out or killed
        if self.hp > 0:
            self.hp -= damage_taken
            if self.hp == 0:
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

    def _roll_hit_points(self) -> int:
        const_mod = self.stats.get_modifier(Ability.constitution)
        if self.use_average_hp:
            return int((roll(self.stats.hit_die, use_average=True) + const_mod) * self.stats.level)

        hp = sum(
            roll(self.stats.hit_die, use_average=False) + const_mod for _ in range(self.stats.level)
        )
        return max(hp, 1)
