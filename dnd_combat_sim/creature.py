"""Module to define the Creature class and related methods."""

from __future__ import annotations

import logging
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import Collection, List, Optional, Sequence, Union

from dnd_combat_sim.weapon import Weapon, AttackDamage, AttackRoll, DamageType
from dnd_combat_sim.dice import roll, roll_d20
from dnd_combat_sim.rules import (
    Ability,
    Condition,
    CreatureType,
    DamageOutcome,
    Point,
    Sense,
    Size,
    Skill,
    SKILL_MAPPING,
)
from dnd_combat_sim.utils import MONSTERS, get_distance

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
        abilities: Union[Abilities, list[int]] = Abilities(10, 10, 10, 10, 10, 10),
        actions: Optional[Sequence[str]] = None,  # Optional non-attack actions, e.g. teleport
        attack_bonus: Optional[int] = None,  # Overrides proficiency + mods if provided
        attacks: Sequence[Union[Weapon, str]] = None,
        cond_immunities: Optional[Collection[Condition]] = None,
        cr: Optional[float] = None,
        creature_subtype: Optional[str] = None,  # No mechanical meaning?
        creature_type: Optional[CreatureType] = None,
        different_attacks: bool = True,
        has_shield: bool = False,  # Relevant for using two-handed weapons
        immunities: Optional[Collection[DamageType]] = None,
        make_death_saves: bool = False,
        num_attacks: int = 1,
        num_hands: int = 2,
        proficiency: Optional[int] = None,  # Can be inferred from CR
        resistances: Optional[Collection[DamageType]] = None,
        save_proficiencies: Optional[Collection[Union[Ability, str]]] = None,
        senses: Optional[Union[Collection[Sense], dict[Sense, int]]] = None,
        size: Optional[Union[Size, str]] = None,  # Can infer from hit die type if not provided
        skill_proficiencies: Optional[Collection[Skill]] = None,
        skill_expertises: Optional[Collection[Skill]] = None,
        speed: int = 30,
        speed_fly: int = 0,
        speed_hover: int = 0,
        speed_swim: int = 0,
        # spell_slots: dict[int, int] = None,
        # spells: list[str] = None,
        traits: List[str] = None,
        vulnerabilities: Optional[Collection[DamageType]] = None,
    ) -> None:
        """Create a creature.

        Args:
            name: What to call the creature.
            ac: Armour class.
            hp: Max hit points, either absolute int or dice to roll, e.g. "5d6", for 5x 6-sided die.
            abilities: Ability scores, in order STR, DEX, CON, INT, WIS, CHA.
            attack_bonus: Override for proficiency bonus + attack modifier for all attacks.
            attacks: List of attacks the creature can make.
            cond_immunities: Conditions the creature is immune to.
            cr: Challenge rating. Used to infer proficiency if not provided.
            creature_subtype: E.g. "goblinoid", "demon", "shapeshifter".
            creature_type: E.g. "humanoid", "fiend", "undead".
            different_attacks: Whether a creature must use different attacks on a given turn when
                `num_attacks` > 1.
            has_shield: Whether the creature has a shield equipped. Relevant for two-handed attacks.
            immunities: Damage types the creature is immune to.
            make_death_saves: Whether the creature should make death saving throws when reduced to
                0 HP (e.g. player characters) or die outright (e.g. standard monsters).
            num_attacks: Number of attacks the creature can make on its turn.
            num_hands: Number of hands the creature has. Relevant for two-handed attacks.
            proficiency: Proficiency bonus to apply for attacks, saving throws etc. Can be inferred
                from CR if not provided.
            resistances: Damage types the creature is resistant to.
            save_proficiencies: Ability saving throws for which the creature is proficient.
            senses: Senses the creature has, e.g. darkvision, blindsight, tremorsense. Not currently
                used for anything.
            size: Size of the creature, e.g. "small", "medium", "large". If not provided, can be
                inferred from `hp` if provided as a string.
            skill_proficiencies: Skills the creature is proficient in.
            skill_expertises: Skills the creature has expertise in (i.e. double proficiency).
            speed: Movement speed in feet.
            speed_fly: Flying speed in feet.
            speed_hover: Hovering speed in feet.
            speed_swim: Swimming speed in feet.
            traits: List of keys for traits the creature has, e.g. undead_fortitude. See `TRAITS` in
                _traits.py_.
            vulnerabilities: Damage types the creature is vulnerable to.
        """
        self.name = name
        self.ac = ac
        self.abilities = Abilities(*abilities) if isinstance(abilities, list) else abilities
        self.actions = actions
        self.cr = cr
        # Parse hit points
        if isinstance(hp, str):
            self.num_hit_die, self.hit_die = map(int, hp.split("d"))  # E.g. "5d6" -> (5, 6)
            self.hp = self.max_hp = self._roll_hit_points()
        else:
            self.num_hit_die, self.hit_die = None, None
            self.hp = self.max_hp = hp
        # Parse size
        if size is None and self.hit_die is not None:
            size = {
                6: Size.small,
                8: Size.medium,
                10: Size.large,
                12: Size.huge,
                20: Size.gargantuan,
            }[self.hit_die]
        elif isinstance(size, str):
            size = Size[size]
        self.size = size
        # Parse proficiency
        if proficiency is None:
            if cr is not None:
                # DMG maps challenge rating to suggested proficiency bonus
                proficiency = max(cr - 1, 0) // 4 + 2
            else:
                raise ValueError("Must provide at least one of ['proficiency', 'cr']")

        self.attack_bonus = attack_bonus
        if attacks is not None:
            self.attacks = [
                Weapon.init(attack, size=self.size) if isinstance(attack, str) else attack
                for attack in attacks
            ]
        if creature_type == CreatureType.humanoid:
            self.attacks.append(Weapon.init("unarmed_strike"))
        self.cond_immunities = cond_immunities or set()
        self.creature_subtype = creature_subtype
        self.creature_type = creature_type
        self.different_attacks = different_attacks
        self.has_shield = has_shield
        self.immunities = immunities or set()
        self.make_death_saves = make_death_saves
        self.num_attacks = num_attacks
        self.num_hands = num_hands
        self.position = Point(5, 5)
        self.proficiency = proficiency
        self.resistances = resistances or set()
        self.save_proficiencies = {
            Ability[save] if isinstance(save, str) else save
            for save in (save_proficiencies or [])
            if save
        }
        self.senses = senses or set()
        self.skill_proficiencies = {
            Skill[skill] if isinstance(skill, str) else skill
            for skill in (skill_proficiencies or [])
            if skill
        }
        self.skill_expertises = {
            Skill[skill] if isinstance(skill, str) else skill
            for skill in (skill_expertises or [])
            if skill
        }
        self.speed = speed
        self.speed_fly = speed_fly
        self.speed_hover = speed_hover
        self.speed_swim = speed_swim
        # self.spell_slots_total = spell_slots or {}
        # self.spell_slots = spell_slots_total.copy() if spell_slots
        self.traits = traits or []
        self.vulnerabilities = vulnerabilities or set()

        # Combat stuff
        self.remaining_movement: int = speed
        self.attack_used: bool = False
        self.weapons_used_this_turn: set[Weapon] = set()
        self.bonus_action_used: bool = False
        self.reaction_used: bool = False
        self.conditions: set[Condition] = set()
        self.temp_hp: int = 0
        self.death_saves: dict[str, int] = {"successes": 0, "failures": 0}

    @classmethod
    def init(
        cls, monster: str, name: Optional[str] = None, make_death_saves: bool = False
    ) -> Creature:
        """Create a creature from a monster template."""
        stats = MONSTERS.loc[monster].to_dict()

        # Parse fields that need it
        stats["name"] = monster.title() if name is None else name.title()
        stats["abilities"] = [stats.pop(ability) for ability in Ability.__members__]
        size = Size[stats["size"]]
        stats["size"] = size
        stats["attacks"] = [
            Weapon.init(attack, size=size) for attack in (stats["attacks"] or "").split(",")
        ]
        stats["creature_type"] = CreatureType[stats["creature_type"]]
        stats["make_death_saves"] = make_death_saves
        if stats["senses"]:
            stats["senses"] = [Sense[sense] for sense in stats["senses"].split(",")]

        for key in [
            "cond_immunities",
            "immunities",
            "resistances",
            "save_proficiencies",
            "skill_proficiencies",
            "skill_expertises",
            "traits",
            "vulnerabilities",
        ]:
            stats[key] = stats[key].split(",") if stats[key] else None

        return cls(**stats)

    def __repr__(self) -> str:
        return f"{self.name} ({self.hp}/{self.max_hp})"

    def choose_action(self) -> tuple[str, Optional[str]]:
        """Choose an action and bonus action for the turn."""
        action = random.choice(["attack"])
        bonus_action = random.choice([None])

        return action, bonus_action

    def choose_weapon(self, _targets: list[Creature]) -> Weapon:
        """Choose an attack to use against a target.

        For now, simpply choose the attack with the highest expected damage, not factoring in
        likelihood to hit, advantage/disadvantage, resistances or anything else.
        """
        attack_options = []
        expected_damages = []
        available_hands = self.num_hands - 1 if self.has_shield else self.num_hands
        two_handed = available_hands >= 2
        for attack in self.attacks:
            if attack.quantity < 1 or (
                self.different_attacks and attack.name in self.weapons_used_this_turn
            ):
                continue

            # Ignore different damage types for now
            expected_damage = attack.roll_damage(two_handed=two_handed, use_average=True).total
            attack_options.append(attack)
            expected_damages.append(expected_damage)

        return random.choices(attack_options, weights=expected_damages)[0]

    def get_damage_taken(self, attack_damage: AttackDamage) -> AttackDamage:
        """Apply immunities, resistances and vulnerabilities to update attack damage."""
        attack_damage = deepcopy(attack_damage)
        for dtype in attack_damage.damages:
            if dtype in self.immunities:
                attack_damage.damages.pop(dtype)
            elif dtype in self.vulnerabilities:
                attack_damage.damages[dtype] *= 2
            elif dtype in self.resistances:
                attack_damage.damages[dtype] //= 2

        return attack_damage

    def heal(self, amount: int, wake_up: bool = True) -> None:
        """Recover hit points."""
        self.hp = min(self.hp + amount, self.max_hp)
        self.conditions.discard(Condition.dead)
        self.conditions.discard(Condition.dying)
        if wake_up:
            self.conditions.discard(Condition.unconscious)

    def roll_attack(
        self,
        weapon: Weapon,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> AttackRoll:
        """Make an attack roll, returning an AttackRoll describing it."""
        self.attack_used = True
        self.weapons_used_this_turn.add(weapon.name)
        # If firing a projectile or throwing the weapon, decrease the count
        if not weapon.melee:  # TODO or attack.melee and throwing
            weapon.quantity -= 1
            if weapon.quantity == 0:
                span = "ammo for" if weapon.ammunition else ""
                logger.debug(f"{self.name} using up last {span} {weapon.name}!")

        # Roll to attack
        rolled = roll_d20(advantage=advantage, disadvantage=disadvantage)

        if self.attack_bonus is not None:
            modifier = self.attack_bonus
        else:
            modifier = self._get_attack_modifier(weapon)
            modifier += self.proficiency if weapon.proficient else 0

        return AttackRoll(rolled, modifier, self._is_crit(rolled), weapon)

    def roll_check(
        self,
        ability_or_skill: Optional[Collection[Union[Ability, Skill]]] = None,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> int:
        """Roll a skill or ability check."""
        rolled = roll_d20(advantage=advantage, disadvantage=disadvantage)

        modifier = 0
        if ability_or_skill is not None:
            modifier = self._get_modifier(ability_or_skill)

        return rolled + modifier

    def roll_damage(self, attack: Weapon, crit: bool = False) -> AttackDamage:
        """Roll damage for an attack that has hit."""
        # Use two-handed damage if have a spare hand
        damage_modifier = self._get_attack_modifier(attack)

        damage = attack.roll_damage(
            two_handed=self._get_num_free_hands() >= 2,
            crit=crit,
            damage_modifier=damage_modifier,
            use_average=False,
        )
        return damage

    def roll_death_save(self) -> tuple[int, str]:
        """Roll a death saving throw.

        Return the roll and result."""
        death_save = roll_d20()

        if death_save == 1:
            result = "critical failure"
            self.death_saves["failures"] += 2
        elif 2 <= death_save <= 9:
            result = "failure"
            self.death_saves["failures"] += 1
        elif 10 <= death_save <= 19:
            result = "success"
            self.death_saves["successes"] += 1
            if self.death_saves["successes"] == 3:
                result = "stabilised"
                self.conditions.add(Condition.stable)
                self._reset_death_saves()
        elif death_save == 20:
            result = "critical success"
            self.heal(1, wake_up=True)
            self._reset_death_saves()

        if self.death_saves["failures"] >= 3:
            self._die()
            result = "death"

        return death_save, result

    def roll_initiative(self):
        """Roll initiative for the creature."""
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
        """Create a new copy of this creature with the same stas but statuses reset."""
        new_creature = deepcopy(self)
        if name is not None:
            new_creature.name = name

        # Roll new HP; reset spell slots, conditions and death saves
        if self.num_hit_die is not None:
            new_creature.hp = new_creature.max_hp = self._roll_hit_points()
        else:
            new_creature.hp = new_creature.max_hp
        new_creature.start_turn()
        # new_creature.spell_slots = self.total_spell_slots.copy()
        new_creature.conditions = set()
        new_creature.death_saves = {"successes": 0, "failures": 0}

        return new_creature

    def start_turn(self) -> None:
        """Indicate the start of a new turn, reset transient state."""
        self.remaining_movement = self.speed
        self.attack_used = False
        self.weapons_used_this_turn = set()
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
    ) -> DamageOutcome:
        """Take damage from a hit and return the outcome of the damage."""
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
    def _check_if_can_grapple(self, target: Creature) -> bool:
        """Check if the creature can grapple a target.

        Must have at least 1 free hand, be within reach, and target can't be more than 1 size
        larger.
        """
        return any(
            ((target.size - self.size) > 1),
            (self._get_num_free_hands() < 1),
            (get_distance(self.position, target.position) > 5),
        )

    def _die(self) -> str:
        self.conditions.add(Condition.dead)
        self.conditions.discard(Condition.dying)
        self.conditions.discard(Condition.unconscious)

        return DamageOutcome.dead

    def _get_attack_modifier(self, attack: Weapon) -> int:
        """Get an attack modifier:

        - strength for melee attacks
          - or dexterity for finesse weapons (whichever is higher)
        - dexterity for ranged attacks
          - or strength for thrown weapons, or either for thrown finesse weapons
        """
        if attack.finesse:
            return self._get_modifier([Ability.str, Ability.dex])
        if attack.melee:
            return self._get_modifier(Ability.str)

        return self._get_modifier(Ability.dex)

    def _get_modifier(
        self, skill_or_ability: Union[Ability, Skill, Collection[Union[Ability]]]
    ) -> int:
        """Get the modifier for an ability or skill.

        If multiple skills or abilities are passed, return whichever modifier is highest.
        """
        if isinstance(skill_or_ability, (Ability, Skill)):
            skill_or_ability = [skill_or_ability]

        best_modifier = -5
        for option in skill_or_ability:
            if isinstance(option, Ability):
                ability = option
                skill = None
            if isinstance(option, Skill):
                skill = option
                ability = SKILL_MAPPING[option]

            modifier = (getattr(self.abilities, ability.name) - 10) // 2
            if skill is not None:
                if skill in self.skill_expertises:
                    modifier += self.proficiency * 2
                elif skill in self.skill_proficiencies:
                    modifier += self.proficiency
            if modifier > best_modifier:
                best_modifier = modifier

        return best_modifier

    def _get_num_free_hands(self, grappling: bool = False):
        """Get number of free hands available. Assume that a shield is always being held, but any
        weapon can be sheathed or unsheathed as a free object interaction.
        """
        free_hands = self.num_hands
        if self.has_shield:
            free_hands -= 1
        if grappling:
            free_hands -= 1

        return free_hands

    def _is_crit(self, rolled: int):
        """Other rules can apply, e.g. with certain feats."""
        return rolled == 20

    def _reset_death_saves(self, wake_up: bool = False):
        self.death_saves = {"successes": 0, "failures": 0}
        self.conditions.discard(Condition.dying)
        if wake_up:
            self.conditions.discard(Condition.unconscious)

    def _roll_hit_points(self) -> int:
        dice = f"{self.num_hit_die}d{self.hit_die}"
        const_mod = self.abilities.get_modifier(Ability.con)
        hp = roll(dice) + const_mod * self.num_hit_die

        return int(max(hp, 1))
