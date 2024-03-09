import re
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Optional

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
    num_dice: int
    die_size: int
    damage_type: DamageType

    def expected_damage(self) -> float:
        """Return the expected damage of the attack."""
        return (self.die_size + 1) / 2 * self.num_dice


class Property(StrEnum):
    ammunition = auto()
    loading = auto()
    finesse = auto()  # Means can use dex instead of str
    heavy = auto()  # Means disadvantage if small
    light = auto()  # Means can 2-hand


@dataclass
class Attack:
    """An attack that a creature can make."""

    name: str
    reach: Optional[int] = None  # melee attack if not None
    range: Optional[tuple[int, int]] = None  # Normal range / long range, in feet
    damage: Optional[str] = None  # E.g. "1d8 bludgeoning", "3d6"
    two_handed_damage: Optional[Damage] = None
    bonus_damage: Optional[str] = None
    _damage: Optional[Damage] = field(default=None, init=False)
    _two_handed_damage: Optional[Damage] = field(default=None, init=False)
    _bonus_damage: Optional[Damage] = field(default=None, init=False)
    proficient: bool = True
    ammunition: bool = False
    finesse: bool = False
    heavy: bool = False
    light: bool = False
    loading: bool = False

    def expected_damage(self, two_handed: bool = False) -> float:
        """Return the average damage of the attack."""
        if two_handed and self._two_handed_damage is not None:
            expected = self._two_handed_damage.expected_damage()
        elif self._damage is not None:
            expected = self._damage.expected_damage()

        if self._bonus_damage is not None:
            expected += self._bonus_damage.expected_damage()

        return expected

    def __post_init__(self) -> None:
        if self.damage:
            self._damage = self._parse_damage(self.damage)
        if self.two_handed_damage:
            self._two_handed_damage = self._parse_damage(self.two_handed_damage)

    def _parse_damage(self, damage: str) -> Damage:
        """Parse the damage string into a Damage object."""
        match = re.match(DAMAGE_PATTERN, damage)

        err_msg = f"Invalid damage string: {damage}. Expected e.g. '2d6 force'."
        if not match or len(match.groups()) < 2:
            raise ValueError(err_msg)

        num_dice = int(match.groups()[0])
        die_size = int(match.groups()[1])

        if len(match.groups()) == 2:
            return Damage(int(num_dice), int(die_size))

        # Damage type is included
        damage_type = match.groups()[2]
        if damage_type not in DamageType:
            raise ValueError(f"Invalid damage type: {damage_type}.")
        return Damage(int(num_dice), int(die_size), DamageType[damage_type])


class MeleeAttack(Attack):
    def __init__(
        self,
        name: str,
        damage: Optional[str] = None,
        two_handed_damage: Optional[str] = None,
        bonus_damage: Optional[str] = None,
        reach: int = 5,
        range: Optional[tuple[int]] = None,  # Indicates can be thrown
        proficient: bool = True,
        finesse: bool = False,
        light: bool = False,
        heavy: bool = False,
    ):
        super().__init__(
            name=name,
            reach=reach,
            range=range,
            damage=damage,
            two_handed_damage=two_handed_damage,
            bonus_damage=bonus_damage,
            proficient=proficient,
            finesse=finesse,
            heavy=heavy,
            light=light,
        )


class RangedAttack(Attack):
    def __init__(
        self,
        name: str,
        damage: Optional[str] = None,
        bonus_damage: Optional[str] = None,
        range: tuple[int] = (30, 120),
        proficient: bool = True,
        thrown: bool = False,
        heavy: bool = False,
        loading: bool = False,
    ):
        """Create a ranged attack.

        If `thrown` is False, weapon is assumed to use ammunition.
        """

        super().__init__(
            name=name,
            range=range,
            damage=damage,
            bonus_damage=bonus_damage,
            proficient=proficient,
            ammunition=not thrown,
            heavy=heavy,
            loading=loading,
        )
