from dataclasses import dataclass
from enum import StrEnum, auto


class Ability(StrEnum):
    """Character abilities."""

    str = auto()
    dex = auto()
    con = auto()
    int = auto()
    wis = auto()
    cha = auto()


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


class Sense(StrEnum):
    """Creature senses."""

    blindsight = auto()
    darkvision = auto()
    tremorsense = auto()
    truesight = auto()


class Type(StrEnum):
    """Creature types."""

    aberration = auto()
    beast = auto()
    celestial = auto()
    construct = auto()
    dragon = auto()
    elemental = auto()
    fey = auto()
    fiend = auto()
    giant = auto()
    humanoid = auto()
    monstrosity = auto()
    ooze = auto()
    plant = auto()
    undead = auto()


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
