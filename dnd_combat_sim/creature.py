from __future__ import annotations

import logging
import random
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Collection, List, Optional, Union

from dnd_combat_sim.attack import Attack, AttackDamage, AttackRoll, DamageOutcome, DamageType
from dnd_combat_sim.conditions import Condition
from dnd_combat_sim.dice import roll, roll_d20
from dnd_combat_sim.rules import Ability, CreatureType, Sense, Size, Skill
from dnd_combat_sim.utils import MONSTERS

logger = logging.getLogger(__name__)


@dataclass
class Abilities:
    """Class to store ability scores and modifiers."""

    str: int
    dex: int
    con: int
    int: int
    wis: int
    cha: int

    def get_modifier(self, ability: Ability) -> int:
        """Get the modifier for an ability score."""
        score = getattr(self, ability.name)
        return (score - 10) // 2


class Creature:
    """Class to store all state for a creature."""

    def __init__(
        self,
        name: str,
        ac: int,
        hp: Union[str, int],  # e.g. '5d6' or 16
        abilities: Union[Abilities, list[int]],
        save_proficiencies: Optional[Collection[Union[Ability, str]]] = None,
        skill_proficiencies: Optional[Collection[Skill]] = None,
        skill_expertises: Optional[Collection[Skill]] = None,
        vulnerabilities: Optional[Collection[DamageType]] = None,
        resistances: Optional[Collection[DamageType]] = None,
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
        type: Optional[CreatureType] = None,
        subtype: Optional[str] = None,  # No mechanical meaning?
        make_death_saves: bool = False,
        use_average_hp: bool = False,
    ) -> None:
        """Create a creature.

        Args:
            name: What to call the creature.
            ac: Armour class.
            hp: Max hit points, either absolute or die to roll, e.g. "5d6", for 5x 6-sided die.
        """
        self.name = name
        self.ac = ac
        self.abilities = Abilities(*abilities) if isinstance(abilities, list) else abilities

        self.use_average_hp = use_average_hp
        if isinstance(hp, str):
            self.hit_dice = hp
            self.hp = self.max_hp = self._roll_hit_points()
        else:
            self.hit_dice = None
            self.hp = self.max_hp = hp

        saves = save_proficiencies or []
        saves = {Ability[save] if isinstance(save, str) else save for save in saves}
        self.save_proficiencies = saves
        self.skill_proficiencies = skill_proficiencies or set()
        self.skill_expertises = skill_expertises or set()
        self.vulnerabilities = vulnerabilities or set()
        self.resistances = resistances or set()
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
        if type == CreatureType.humanoid:
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

        # Combat stuff
        self.remaining_movement = speed
        self.attack_used: bool = False
        self.attacks_used_this_turn = set()
        self.bonus_action_used = False
        self.reaction_used = False
        self.conditions = set()
        self.temp_hp: int = 0
        self.death_saves = {"successes": 0, "failures": 0}

    @classmethod
    def init(
        cls, monster: str, name: Optional[str] = None, make_death_saves: bool = False
    ) -> Creature:
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
            # save_proficiencies=[] stats["save_proficiencies"],
            # skill_proficiencies=skills,
            cr=stats["cr"],
            proficiency=stats["proficiency"],
            traits=(stats["traits"] or "").split(","),
            attacks=attacks,
            has_shield=stats["has_shield"],
            num_attacks=stats["num_attacks"],
            resistances=stats["resistances"],
            vulnerabilities=stats["vulnerabilities"],
            immunities=stats["immunities"],
            make_death_saves=make_death_saves,
        )

    def __repr__(self) -> str:
        return f"{self.name} ({self.hp}/{self.max_hp})"

    def choose_action(self) -> tuple[str, Optional[str]]:
        """Choose an action and bonus action for the turn."""
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
            if attack.quantity < 1 or (
                self.different_attacks and attack.name in self.attacks_used_this_turn
            ):
                continue

            expected_damages = attack.roll_damage(two_handed=two_handed, use_average=True)
            # Ignore different damage types for now
            expected_damage = sum(expected_damages.damages.values())
            attack_options[expected_damage].append(attack)

        # Sort from highest expected damage to lowest
        attack_options = dict(sorted(attack_options.items(), reverse=True))
        best_options = attack_options[list(attack_options.keys())[0]]
        return random.choice(best_options)

    def heal(self, amount: int, wake_up: bool = True) -> None:
        self.hp = min(self.hp + amount, self.max_hp)
        self.conditions.discard(Condition.dead)
        self.conditions.discard(Condition.dying)
        if wake_up:
            self.conditions.discard(Condition.unconscious)

    def modify_damage(self, attack_damage: AttackDamage) -> AttackDamage:
        """Modify the damage dealt by an attack."""
        for dtype in attack_damage.damages:
            if dtype in self.immunities:
                # logger.debug(f"{self.name} is immune to {str(dtype)} damage.")
                attack_damage.damages.pop(dtype)
            elif dtype in self.vulnerabilities:
                # logger.debug(f"{self.name} is vulnerable to {str(dtype)} damage.")
                attack_damage.damages[dtype] *= 2
            elif dtype in self.resistances:
                # logger.debug(f"{self.name} is resistant to {str(dtype)} damage.")
                attack_damage.damages[dtype] //= 2

        # TODO handle conditions and traits

        return attack_damage

    def roll_attack(
        self, attack: Attack, advantage: bool = False, disadvantage: bool = False
    ) -> AttackRoll:
        """Make an attack roll.

        Return a tuple of (attack total, d20 roll, modifiers, whether is a crit)
        """
        self.attack_used = True
        self.attacks_used_this_turn.add(attack.name)
        # If firing a projectile or throwing the weapon, decrease the count
        if not attack.melee:  # TODO or attack.melee and throwing
            attack.quantity -= 1
            if attack.quantity == 0:
                span = "ammo for" if attack.ammunition else ""
                logger.debug(f"{self.name} using up last {span} {attack.name}!")

        # Roll to attack
        attack_roll = roll_d20(advantage=advantage, disadvantage=disadvantage)

        ability_mod = self._get_attack_modifier(attack)
        proficiency_bonus = self.proficiency if attack.proficient else 0

        return AttackRoll(attack_roll, ability_mod + proficiency_bonus, self._is_crit(attack_roll))

    def roll_damage(self, attack: Attack, crit: bool = False) -> AttackDamage:
        """Roll damage for an attack that has hit."""
        # Use two-handed damage if have a spare hand
        damage_modifier = self._get_attack_modifier(attack)

        available_hands = self.num_hands - 1 if self.has_shield else self.num_hands
        can_use_two_handed = available_hands >= 2
        damage = attack.roll_damage(
            two_handed=can_use_two_handed,
            crit=crit,
            damage_modifier=damage_modifier,
            use_average=False,
        )
        return damage

    def roll_death_save(self) -> tuple[int, str]:
        """Roll a death saving throw.

        Return the roll and result."""
        roll = roll_d20()

        if roll == 20:
            result = "critical success"
            self.heal(1)
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
                self._die()
                result = "death"

        return roll, result

    def roll_initiative(self):
        return roll_d20() + self.abilities.get_modifier(Ability.dex)

    def roll_saving_throw(
        self, ability: Ability, advantage: bool = False, disadvantage: bool = False
    ) -> int:
        """Roll a saving throw for a given ability."""
        save = roll_d20(advantage=advantage, disadvantage=disadvantage)
        modifier = self.abilities.get_modifier(ability)
        if ability in self.save_proficiencies:
            modifier += self.proficiency

        return save + modifier

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

    def start_turn(self) -> None:
        self.remaining_movement = self.speed
        self.attack_used = False
        self.attacks_used_this_turn = set()
        self.bonus_action_used = False
        self.reaction_used = False

        if Condition.dying in self.conditions:
            value, result = self.roll_death_save()
            logger.debug(
                f"{self.name} rolled a {value} on their death saving throw: {result}\n"
                f"{self.death_saves}."
            )
            if result == "death":
                logger.debug(f"{self.name} is DEAD!")

    def take_damage(
        self,
        damage: AttackDamage,
        crit: bool = False,
        # modifier: Optional[Callable[[AttackDamage], AttackDamage]] = None
    ) -> str:
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
        total_damage = damage.total

        damage_taken = min(total_damage, self.hp)
        excess_damage = total_damage - damage_taken
        self.hp -= damage_taken

        # Check for instant death
        if excess_damage > self.max_hp:
            self._die()
            return DamageOutcome.instant_death

        if self.hp > 0:
            return DamageOutcome.alive

        if Condition.dying not in self.conditions:
            if self.make_death_saves:
                self.conditions.update([Condition.unconscious, Condition.dying])
                return DamageOutcome.knocked_out
            else:
                return self._die()
        else:
            # Already making death saving throws, get failure(s) instead of damage
            self.death_saves["failures"] += 1 if not crit else 2
            if self.death_saves["failures"] >= 3:
                return self._die()
            return DamageOutcome.still_dying

    # Private methods
    def _die(self) -> str:
        self.conditions.add(Condition.dead)
        self.conditions.discard(Condition.dying)
        self.conditions.discard(Condition.unconscious)

        return DamageOutcome.dead

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
        self.num_hit_die, self.hit_die = map(int, self.hit_dice.split("d"))

        const_mod = self.abilities.get_modifier(Ability.con)
        if self.use_average_hp:
            return int((roll(self.hit_die, use_average=True) + const_mod) * self.num_hit_die)

        hp = sum(roll(self.hit_die, use_average=False) + const_mod for _ in range(self.num_hit_die))
        return max(hp, 1)
