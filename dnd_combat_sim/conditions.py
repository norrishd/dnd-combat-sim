from enum import StrEnum, auto


class Condition(StrEnum):
    """Possible conditions."""

    blinded = auto()
    charmed = auto()
    deafened = auto()
    frightened = auto()
    grappled = auto()
    incapacitated = auto()
    invisible = auto()
    paralyzed = auto()
    petrified = auto()
    poisoned = auto()
    prone = auto()
    restrained = auto()
    stunned = auto()
    unconscious = auto()
    dying = auto()
    dead = auto()
