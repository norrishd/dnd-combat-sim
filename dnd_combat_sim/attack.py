from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Union

from dnd_combat_sim.dice import roll
from dnd_combat_sim.rules import DamageType, Size
from dnd_combat_sim.utils import ATTACKS


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

    def __repr__(self) -> str:
        return f"{self.dice} {str(self.damage_type)}"


@dataclass
class DamageRolled:
    """Class to represent an actual amount of damage rolled and its associated type.

    E.g. 15 thunder damage.
    """

    amount: Union[int, float]
    damage_type: DamageType

    def __post_init__(self) -> None:
        self.amount = int(self.amount)


class AttackDamage:
    """Class to represent the total damage deal from an attack that hits, including one or more
    damage types.
    """

    def __init__(self, damages_rolled: list[DamageRolled]) -> None:
        self.damage: dict[DamageType, int] = defaultdict(int)
        for damage_rolled in damages_rolled:
            self.damage[damage_rolled.damage_type] += damage_rolled.amount

    def __repr__(self) -> str:
        return " + ".join(f"{amount} {damage_type}" for damage_type, amount in self.damage.items())


@dataclass(repr=False)
class Attack:
    """Base class for an attack that a creature can make."""

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
    proficient: bool = True  # Specific to the wielder

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
        attack = ATTACKS.loc[key].copy()

        # Larger creatures use larger weapons which multiply the number of dice rolled.
        # See DMG 'Creating a Monster Stat Block' p278
        if attack["is_weapon"] and size > Size.medium:
            for damage in ["damage", "two_handed_damage"]:
                dice, damage_type = damage.split(" ")
                num_dice, die_size = map(int, dice.split("d"))

                if size == Size.large:
                    num_dice = num_dice * 2
                elif size == Size.huge:
                    num_dice = num_dice * 3
                elif size == Size.gargantuan:
                    num_dice = num_dice * 4

                attack[damage] = DamageRoll(f"{num_dice}d{die_size}", DamageType[damage_type])

        return cls(
            name=attack["name"],
            melee=attack["melee"],
            damage=attack["damage"],
            two_handed_damage=attack["two_handed_damage"],
            bonus_damage=attack["bonus_damage"],
            range=(attack["range"], attack["range_long"]) if attack["range"] else None,
            is_weapon=attack["is_weapon"],
            type=attack["type"],
            ammunition=attack["ammunition"],
            finesse=attack["finesse"],
            heavy=attack["heavy"],
            light=attack["light"],
            loading=attack["loading"],
            reach=attack["reach"],
            thrown=attack["thrown"],
            trait=attack["trait"],
            quantity=quantity,
            recharge=attack["recharge"],
            size=size,
            proficient=proficient,
        )

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
            all_damages.append(DamageRolled(damage_rolled, damage_roll.damage_type))

        if self.bonus_damage is not None:
            damage_rolled = roll(self.bonus_damage.dice, crit=crit, use_average=use_average)
            all_damages.append(DamageRolled(damage_rolled, self.bonus_damage.damage_type))

        return AttackDamage(all_damages)

    def __repr__(self) -> str:
        ret = f"{self.name}:"
        if self.is_weapon:
            if self.type in ["simple", "martial"]:
                ret += f" {self.type} "
        ret += f" {'melee' if self.melee else ' ranged'} weapon attack."

        if self.melee:
            ret += f" Reach {10 if self.reach else 5} ft"
            if self.thrown:
                ret += f", range {self.range[0]}/{self.range[1]} ft thrown."
        else:
            ret += f" Range {self.range[0]}/{self.range[1]} ft."

        if self.damage or self.two_handed_damage or self.bonus_damage:
            ret += " Hit: "
            if self.damage:
                ret += self.damage
                if self.two_handed_damage:
                    ret += f" ({self.two_handed_damage.dice} for two-handed)"
            elif self.two_handed_damage:
                ret += self.two_handed_damage
            if self.bonus_damage:
                if self.damage or self.two_handed_damage:
                    ret += " + "
                ret += self.bonus_damage

        if self.ammunition or self.thrown:
            ret += f". Quantity={self.quantity}"

        return ret
