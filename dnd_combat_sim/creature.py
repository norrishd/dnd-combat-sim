from __future__ import annotations

import random
from collections import defaultdict
from copy import deepcopy
from typing import Collection, List, Optional, Union

from dnd_combat_sim.attack import Attack, DamageType
from dnd_combat_sim.conditions import Condition
from dnd_combat_sim.dice import roll, roll_d20
from dnd_combat_sim.rules import Abilities, Ability, Sense, Size, Skill, Type
from dnd_combat_sim.utils import MONSTERS


class Creature:
    """Class to store all state for a creature."""

    def __init__(
        self,
        name: str,
        ac: int,
        hp: str,  # e.g. 5d6
        abilities: Union[Abilities, list[int]],
        save_proficiencies: Optional[Collection[Ability]] = None,
        skill_proficiencies: Optional[Collection[Skill]] = None,
        skill_expertises: Optional[Collection[Skill]] = None,
        vulnerabilities: Optional[Collection[DamageType]] = None,
        immunities: Optional[Collection[DamageType]] = None,
        cond_immunities: Optional[Collection[Condition]] = None,
        senses: Optional[Union[Collection[Sense], dict[Sense, int]]] = None,
        cr: Optional[float] = None,
        proficiency: Optional[int] = None,  # Can be inferred from CR
        attack_bonus: Optional[int] = None,  # Overrides proficiency + mods if provided
        traits: List[str] = None,
        attacks: list[Union[Attack, str]] = None,
        # actions: list[Action] = None,
        has_shield: bool = False,  # Relevant for using two-handed weapons
        num_attacks: int = 1,
        different_attacks: bool = True,
        num_hands: int = 2,
        speed: int = 30,
        speed_fly: int = 0,
        speed_hover: int = 0,
        speed_swim: int = 0,
        # spell_slots: dict[str, int] = None,
        # spells: list[Spell] = None,
        size: Optional[Size] = None,  # Can infer from hit die type
        type: Optional[Type] = None,
        subtype: Optional[str] = None,  # No mechanical meaning?
        make_death_saves: bool = False,
        use_average_hp: bool = False,
    ) -> None:
        """Create a creature.

        Args:
        """
        self.name = name
        self.ac = ac
        self.num_hit_die, self.hit_die = map(int, hp.split("d"))
        self.abilities = Abilities(*abilities) if isinstance(abilities, list) else abilities
        self.saving_throw_proficiencies = save_proficiencies or set()
        self.skill_proficiencies = skill_proficiencies or set()
        self.skill_expertises = skill_expertises or set()
        self.vulnerabilities = vulnerabilities or set()
        self.immunities = immunities or set()
        self.cond_immunities = cond_immunities or set()
        self.senses = senses or set()
        assert cr is not None or proficiency is not None, "Must provide CR or proficiency"
        self.cr = cr
        self.proficiency = proficiency or max(cr - 1, 0) // 4 + 2
        self.attack_bonus = attack_bonus
        self.traits = traits or []
        # Parse attacks
        self.attacks = [
            Attack.init(attack) if isinstance(attack, str) else attack for attack in attacks
        ]
        if type == Type.humanoid:
            self.attacks.append(Attack.init("unarmed strike"))
        self.has_shield = has_shield
        self.num_hands = num_hands
        self.num_attacks = num_attacks
        self.different_attacks = different_attacks
        self.speed = speed
        self.speed_fly = speed_fly
        self.speed_hover = speed_hover
        self.speed_swim = speed_swim
        # self.total_spell_slots = spell_slots or {}
        # self.spell_slots = total_spell_slots.copy() if spell_slots
        self.size = size
        self.type_ = type
        self.subtype = subtype
        self.make_death_saves = make_death_saves
        self.use_average_hp = use_average_hp

        # Hit points and temporary hit points
        self.hp = self.max_hp = self._roll_hit_points()

        # Combat stuff
        self.attacks_used_this_turn = set()
        self.conditions = set()
        self.temp_hp: int = 0
        self.death_saves = {"successes": 0, "failures": 0}

    @classmethod
    def init(cls, monster: str, name: Optional[str] = None) -> Creature:
        """Create a creature from a monster template."""
        stats = MONSTERS.loc[monster]

        # Parse fields that need it
        # saves = stats["saving_throw_proficiencies"]
        # saves = saves.split(",") if saves else []
        # skills = stats["skill_proficiencies"]
        # skills = skills.split(",") if skills else []
        attacks = [Attack.init(attack) for attack in stats["attacks"].split(",")]

        return cls(
            name=monster.title() if name is None else name.title(),
            ac=stats["ac"],
            hp=stats["hp"],
            abilities=[stats[ability] for ability in Ability.__members__],
            # saving_throw_proficiencies=saves,
            # skill_proficiencies=skills,
            cr=stats["cr"],
            proficiency=stats["proficiency"],
            attacks=attacks,
            has_shield=stats["has_shield"],
            num_attacks=stats["num_attacks"],
        )

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

    def choose_attack(self, targets: list[Creature]) -> Attack:
        """Choose an attack to use against a target.

        For now, simpply choose the attack with the highest expected damage, not factoring in
        likelihood to hit, advantage/disadvantage, resistances or anything else.
        """
        attack_options = defaultdict(list)
        available_hands = self.num_hands - 1 if self.has_shield else self.num_hands
        two_handed = available_hands >= 2
        for attack in self.attacks:
            if (
                attack.quantity < 1
                or self.different_attacks
                and attack in self.attacks_used_this_turn
            ):
                continue
            expected_damage = attack.roll_damage(two_handed=two_handed, use_average=True)
            attack_options[expected_damage].append(attack)

        # Sort from highest expected damage to lowest
        attack_options = dict(sorted(attack_options.items(), reverse=True))
        best_options = attack_options[list(attack_options.keys())[0]]
        return random.choice(best_options)

    def heal(self, amount: int) -> None:
        self.hp = min(self.hp + amount, self.max_hp)

    def roll_attack(self, attack: Attack) -> tuple[int, int, int, bool]:
        """Make an attack roll.

        Return a tuple of (attack total, d20 roll, modifiers, whether is a crit)
        """
        # If firing a projectile or throwing the weapon, decrease the count
        if attack.ammunition or attack.thrown and not attack.melee:
            attack.quantity -= 1

        # Roll to attack
        attack_roll = roll_d20()

        ability_mod = self._get_attack_modifier(attack)
        proficiency_bonus = self.proficiency if attack.proficient else 0

        total = attack_roll + ability_mod + proficiency_bonus

        return (total, attack_roll, ability_mod + proficiency_bonus, self._is_crit(attack_roll))

    def roll_damage(self, attack: Attack, crit: bool = False) -> int:
        """Roll damage for an attack that has hit."""
        # Use two-handed damage if have a spare hand
        available_hands = self.num_hands - 1 if self.has_shield else self.num_hands
        can_use_two_handed = available_hands >= 2
        dice_damage = attack.roll_damage(
            two_handed=can_use_two_handed, crit=crit, use_average=False
        )
        modifier_damage = self._get_attack_modifier(attack)

        return max(dice_damage + modifier_damage, 0)

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
        return roll_d20() + self.abilities.get_modifier(Ability.dex)

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
        str_modifier = self._get_modifier(Ability.str)
        dex_modifier = self._get_modifier(Ability.dex)

        if attack.finesse:
            return max(str_modifier, dex_modifier)
        if attack.melee:
            return str_modifier

        return dex_modifier

    def _get_modifier(self, ability: Ability) -> int:
        """Get the modifier for an ability score."""
        score = getattr(self.abilities, ability.name)
        return (score - 10) // 2

    def _is_crit(self, roll: int):
        return roll == 20

    def _reset_death_saves(self, wake_up: bool = False):
        self.death_saves = {"successes": 0, "failures": 0}
        self.conditions.discard(Condition.dying)
        if wake_up:
            self.conditions.discard(Condition.unconscious)

    def _roll_hit_points(self) -> int:
        const_mod = self.abilities.get_modifier(Ability.con)
        if self.use_average_hp:
            return int((roll(self.hit_die, use_average=True) + const_mod) * self.num_hit_die)

        hp = sum(roll(self.hit_die, use_average=False) + const_mod for _ in range(self.num_hit_die))
        return max(hp, 1)
