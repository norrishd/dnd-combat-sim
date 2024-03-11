"""Module with classes to represent weapon attacks, damage rolls and attack outcomes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Collection, Optional, Union

from dnd_combat_sim.dice import roll
from dnd_combat_sim.rules import DamageType, Size
from dnd_combat_sim.utils import ATTACKS


class AttackRoll:
    """Class to represent the result of an attack roll to hit, including:

    - rolled component
    - modifier score (e.g. strength or dexterity modifier) and/or proficiency
    - whether the roll was a critical hit.
    """

    def __init__(self, rolled: int, modifier: int, crit: bool) -> None:
        self.total = rolled + modifier
        self.rolled = rolled
        self.modifier = modifier
        self.is_crit = crit

    def __repr__(self) -> str:
        symbol = "+" if self.modifier >= 0 else "-"
        return f"{self.total} ({self.rolled} {symbol} {self.modifier})"


@dataclass
class DamageRoll:
    """Class to represent a damage roll with an associated type, e.g. 3d6 thunder damage."""

    dice: str
    damage_type: DamageType

    @classmethod
    def from_str(cls, damage_str: str) -> DamageRoll:
        """Parse a string like '3d6 thunder' into a `DamageRoll` object."""
        dice, damage_type = damage_str.split(" ")
        return cls(dice, DamageType[damage_type])

    @property
    def num_dice(self) -> int:
        """Get the number of dice to roll."""
        return int(self.dice.split("d")[0])

    @property
    def die_size(self) -> int:
        """Get the size of the dice to roll."""
        return int(self.dice.split("d")[1])

    def __repr__(self) -> str:
        return f"{self.dice} {str(self.damage_type)}"


class AttackDamage:
    """Class to represent the total damage deal from an attack that hits, including one or more
    damage types.
    """

    def __init__(
        self, damages_rolled: list[tuple[int, DamageType]], from_crit: bool = False
    ) -> None:
        self.damages: dict[DamageType, int] = defaultdict(int)
        self.from_crit = from_crit
        for damage_rolled in damages_rolled:
            self.damages[damage_rolled[1]] += damage_rolled[0]

    def __repr__(self) -> str:
        return " + ".join(f"{amount} {damage_type}" for damage_type, amount in self.damages.items())

    @property
    def total(self) -> int:
        """Get the total damage dealt from all damage types."""
        return sum(self.damages.values())


@dataclass(repr=False, eq=False)
class Attack:
    """Base class for an attack that a creature can make.

    Args:
        name: E.g. "slam", "bite", "longsword"
        melee: Whether the attack is a melee attack.
        damage: The damage to roll on a hit, e.g. "1d8 bludgeoning"
        two_handed_damage: The damage to roll on a hit with two hands, e.g. "1d10 slashing". Weapons
            with the 'versatile' property can be wielded with one or two hands, yielding different
            amounts of damage.
        bonus_damage: Extra damage to roll on a hit, e.g. "1d6 fire"
        range: The normal and long range of a ranged weapon, in feet, whether fired or thrown.
        is_weapon: Whether the attack is a weapon attack, as opposed to a natural attack like a
            bite or claw.
        traits: Special effects applied on a hit, e.g. for Net or monster attacks.
    """

    name: str
    melee: bool = True
    damage: Optional[Union[str, DamageRoll]] = None  # E.g. "1d8 bludgeoning"
    two_handed_damage: Optional[Union[str, DamageRoll]] = None
    bonus_damage: Optional[Union[str, DamageRoll]] = None
    range: Optional[tuple[int, int]] = None  # Normal range / long range, in feet
    is_weapon: bool = True  # If False assume a 'natural' weapon like claws, bite etc
    type: Optional[str] = None  # E.g. 'simple', 'martial', 'monster'
    ammunition: bool = False
    finesse: bool = False
    heavy: bool = False
    light: bool = False
    loading: bool = False
    reach: bool = False
    thrown: bool = False
    trait: Optional[list[str]] = None  # E.g. for net or lance TODO
    quantity: Optional[int] = None
    recharge: Optional[str] = None  # E.g. "5-6" or "6"
    size: Size = Size.medium  # Creatures attack with disadvantage using a larger weapon
    proficient: bool = True  # Specific to the wielder - TODO move to Creature
    traits: Optional[Collection[str]] = None

    def __post_init__(self) -> None:
        if isinstance(self.damage, str):
            self.damage = DamageRoll.from_str(self.damage)
        if isinstance(self.two_handed_damage, str):
            self.two_handed_damage = DamageRoll.from_str(self.two_handed_damage)
        if isinstance(self.bonus_damage, str):
            self.bonus_damage = DamageRoll.from_str(self.bonus_damage)

        # Assume 1 melee weapon, or roll default amount of ammo for ranged weapons
        if self.quantity is None:
            if self.melee or not self.is_weapon:
                self.quantity = 1
            else:
                # See intro section of the Monster Manual
                self.quantity = roll("2d10") if self.ammunition else roll("2d4")

    @classmethod
    def init(
        cls,
        key: str,
        proficient: bool = True,
        quantity: Optional[int] = None,
        size: Size = Size.medium,
    ) -> Attack:
        """Initialise an attack from _attacks.csv_.

        If size is larger than medium, increase the number of dice rolled for the damage.
        """
        attack = ATTACKS.loc[key].to_dict()

        # Larger creatures use larger weapons which multiply the number of dice rolled.
        # See DMG 'Creating a Monster Stat Block' p278
        if attack["is_weapon"] and size > Size.medium:
            for damage in ["damage", "two_handed_damage"]:
                if attack[damage] is None:
                    continue
                attack_details: str = attack[damage]
                dice, damage_type = attack_details.split(" ")
                num_dice, die_size = map(int, dice.split("d"))

                if size == Size.large:
                    num_dice = num_dice * 2
                elif size == Size.huge:
                    num_dice = num_dice * 3
                elif size == Size.gargantuan:
                    num_dice = num_dice * 4

                attack[damage] = DamageRoll(f"{num_dice}d{die_size}", DamageType[damage_type])

        attack["conditions"] = attack["conditions"].split(",") if attack["conditions"] else None
        range_long = attack.pop("range_long")
        attack["range"] = (int(attack["range"]), int(range_long)) if attack["range"] else None
        attack.update(dict(proficient=proficient, quantity=quantity, size=size))

        return cls(**attack)

    def roll_damage(
        self,
        two_handed: bool = False,
        crit: bool = False,
        damage_modifier: int = 0,
        use_average: bool = False,
    ) -> AttackDamage:
        """Roll the (average) damage for this attack."""
        all_damages = []

        damage_roll = self.damage
        if two_handed and self.two_handed_damage is not None:
            damage_roll = self.two_handed_damage
        if damage_roll is not None:
            damage_rolled = roll(damage_roll.dice, crit=crit, use_average=use_average)
            damage_rolled = max(damage_rolled + damage_modifier, 0)  # Can't be negative
            all_damages.append((damage_rolled, damage_roll.damage_type))

        if self.bonus_damage is not None:
            damage_rolled = roll(self.bonus_damage.dice, crit=crit, use_average=use_average)
            all_damages.append((damage_rolled, self.bonus_damage.damage_type))

        return AttackDamage(all_damages, from_crit=crit)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Attack):
            return False

        # Don't consider weapons different if they have different amounts of ammo left
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self.__dict__
            if attr != "quantity"
        )

    def __repr__(self) -> str:
        size_str = f"{self.size.name.title()} " if self.size > Size.medium else ""
        ret = f"{size_str}{self.name.title()}:"
        if self.is_weapon:
            if self.type in ["simple", "martial"]:
                ret += f" {self.type}"
        ret += f" {'melee' if self.melee else 'ranged'} weapon attack."

        if self.melee:
            ret += f" Reach {10 if self.reach else 5} ft"
            if self.thrown:
                ret += f", range {self.range[0]}/{self.range[1]} ft thrown."
            else:
                ret += "."
        else:
            ret += f" Range {self.range[0]}/{self.range[1]} ft."

        if self.damage or self.two_handed_damage or self.bonus_damage:
            ret += " Hit: "
            if self.damage:
                ret += repr(self.damage)
                if self.two_handed_damage:
                    ret += f" ({self.two_handed_damage.dice} for two-handed)"
            elif self.two_handed_damage:
                ret += repr(self.two_handed_damage)
            if self.bonus_damage:
                if self.damage or self.two_handed_damage:
                    ret += " + "
                ret += str(self.bonus_damage)

        if self.ammunition:
            ret += f" (ammunition: {self.quantity})"
        elif self.thrown:
            ret += f" (quantity: {self.quantity})"

        return ret
