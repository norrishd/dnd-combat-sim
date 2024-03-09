from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Optional

from dnd_combat_sim.dice import roll
from dnd_combat_sim.rules import Size
from dnd_combat_sim.utils import ATTACKS

# Match e.g. "3d6 bludgeoning" -> ("3", "6", "bludgeoning)
DAMAGE_PATTERN = re.compile(r"([0-9]+)d([0-9]+) (.*)")


class DamageType(StrEnum):
    acid = auto()
    bludgeoning = auto()
    cold = auto()
    fire = auto()
    force = auto()
    lightning = auto()
    necrotic = auto()
    piercing = auto()
    poison = auto()
    psychic = auto()
    radiant = auto()
    slashing = auto()
    thunder = auto()


@dataclass
class Damage:
    dice: str
    damage_type: DamageType


@dataclass
class Attack:
    """Base class for an attack that a creature can make."""

    name: str
    melee: bool = True
    damage: Optional[str] = None  # E.g. "1d8 bludgeoning", "3d6"
    two_handed_damage: Optional[Damage] = None
    bonus_damage: Optional[str] = None
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
    size: Size = Size.medium  # Incraese the num die rolled for larger weapons
    proficient: bool = True  # Specific to the wielder
    _damage: Optional[Damage] = field(default=None, init=False)
    _two_handed_damage: Optional[Damage] = field(default=None, init=False)
    _bonus_damage: Optional[Damage] = field(default=None, init=False)

    def __post_init__(self) -> None:
        # Assume 1 melee
        if self.quantity is None:
            if self.melee or not self.is_weapon:
                self.quantity = 1
            else:
                # Ranged weapon ammo: refer to introduction of the Monster Manual
                self.quantity = roll("2d10") if self.ammunition else roll("2d4")

        if self.damage:
            self._damage = self._parse_damage(self.damage)
        if self.two_handed_damage:
            self._two_handed_damage = self._parse_damage(self.two_handed_damage)
        if self.bonus_damage:
            self._bonus_damage = self._parse_damage(self.bonus_damage)

    @classmethod
    def init(
        cls,
        key: str,
        proficient: bool = True,
        quantity: Optional[int] = None,
        size: Size = Size.medium,
    ) -> Attack:
        """Initialise an attack from _attacks.csv_."""
        attack = ATTACKS.loc[key]

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
        self, two_handed: bool = False, crit: bool = False, use_average: bool = False
    ) -> float:
        """Roll the (average) damage for this attack."""
        damage = 0
        if two_handed and self._two_handed_damage is not None:
            damage = roll(self._two_handed_damage.dice, crit=crit, use_average=use_average)
        elif self._damage is not None:
            damage = roll(self._damage.dice, crit=crit, use_average=use_average)

        if self._bonus_damage is not None:
            damage += roll(self._bonus_damage.dice, crit=crit, use_average=use_average)

        return damage

    def _parse_damage(self, damage: str) -> Damage:
        """Parse the damage string into a Damage object."""
        match = re.match(DAMAGE_PATTERN, damage)

        err_msg = f"Invalid damage string: {damage}. Expected e.g. '2d6 force'."
        if not match or len(match.groups()) < 2:
            raise ValueError(err_msg)

        num_dice = int(match.groups()[0])
        die_size = int(match.groups()[1])

        # Larger weapons for larger creatures roll more dice.
        # See DMG 'Creating a Monster Stat Block' p278
        if self.size == Size.large:
            num_dice = num_dice * 2
        elif self.size == Size.huge:
            num_dice = num_dice * 3
        elif self.size == Size.gargantuan:
            num_dice = num_dice * 4

        damage_string = f"{num_dice}d{die_size}"

        if len(match.groups()) == 2:
            return Damage(damage_string)

        # Damage type is included
        damage_type = match.groups()[2]
        if damage_type not in DamageType:
            raise ValueError(f"Invalid damage type: {damage_type}.")

        return Damage(damage_string, DamageType[damage_type])
