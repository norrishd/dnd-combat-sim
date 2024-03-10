from dataclasses import dataclass
from enum import IntEnum, StrEnum, auto


class Ability(StrEnum):
    """Character abilities."""

    str = auto()
    dex = auto()
    con = auto()
    int = auto()
    wis = auto()
    cha = auto()


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


class DamageExchange:
    """Class to represent a damage roll with an associated type, e.g. 3d6 thunder damage."""

    def __init__(self) -> None:
        """Things to track:

        - creature
        - target
        - attack used
        - damage dealt
        - whether was crit
        - damage taken

        How this can be used: responses to damage, e.g. undead fortitude, etc.
        """
        pass


class Sense(StrEnum):
    """Creature senses."""

    blindsight = auto()
    darkvision = auto()
    tremorsense = auto()
    truesight = auto()


class Size(IntEnum):
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


class CreatureType(StrEnum):
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
