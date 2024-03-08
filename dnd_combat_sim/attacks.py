import re
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional, Union

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


@dataclass
class Attack:
    name: str
    hit: int  # Maybe we can compute this on the creature
    reach: Optional[int] = None
    range: Optional[tuple[int, int]] = None
    damage: Optional[Union[str, DamageType]] = None  # E.g. "1d8 bludgeoning", "3d6"
    two_handed_damage: Optional[Damage] = None
    proficient: bool = True
    finesse: bool = False

    def __post_init__(self) -> None:
        match = re.match(DAMAGE_PATTERN, self.damage)
        err_msg = f"Invalid damage string: {self.damage}. Expected e.g. '2d6 force'."
        if not match or len(match.groups()) < 2:
            raise ValueError(err_msg)

        try:
            num_dice = int(match.groups()[0])
            die_size = int(match.groups()[1])
        except ValueError as err:
            raise ValueError(err_msg) from err
        if len(match.groups()) == 3:
            damage_type = match.groups()[2]
            if damage_type not in DamageType:
                raise ValueError(f"Invalid damage type: {damage_type}.")
            self.damage = Damage(int(num_dice), int(die_size), DamageType[damage_type])
        else:
            self.damage = Damage(int(num_dice), int(die_size))


class MeleeAttack(Attack):
    def __init__(
        self,
        name: str,
        hit: int,
        damage: str,
        reach: int = 5,
        two_handed_damage: Optional[str] = None,
        finesse: bool = False,
    ):
        super().__init__(
            name=name,
            hit=hit,
            reach=reach,
            damage=damage,
            two_handed_damage=two_handed_damage,
            finesse=finesse,
        )


class RangedAttack(Attack):
    def __init__(
        self,
        name: str,
        hit: int,
        range: int = (30, 120),
        damage: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            hit=hit,
            range=range,
            damage=damage,
        )


unarmed_strike = MeleeAttack("Unarmed Strike", hit=5, damage="1d1 bludgeoning")
