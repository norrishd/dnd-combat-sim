"""Concepts and rules for the game."""

from dataclasses import dataclass
from enum import IntEnum, StrEnum, auto


class Condition(StrEnum):
    """Possible conditions, roughly sorted into themes.

    - Charmed: Can't attack or target the charmer with any attack or negative effect. The charmer
        also has advantage on any social checks against the creature.

    - Invisible: Like everyone else is blinded to the creature. Attack rolls have advantage and
        attacks against the creature have disadvantage. Considered heavily obscured so can try to
        hide anywhere, however assumed its general position is known due to noises/footprints etc.

    - Blinded: Automatically fail any ability check relying on vision (e.g. perception).
        Attack rolls against the creature have advantage and the creature's attack rolls have
        disadvantage (unless the creature has another sense like blindsight).
    - Deafened: Automatically fail any ability check relying on hearing.

    - Poisoned: Disadvantage on attack rolls and ability checks.
    - Frightened: Disadvantage on attack rolls and ability checks while the source of fear is within
        line of sight. Also can't willingly move nearer to it.

    - Prone: can only move at half speed (unless use half of movement to stand up). Have
        disadvantage on attack rolls. Attack rolls against the creature made within 5 ft have
        advantage, and otherwise have disadvantage.

    - Grappled: Speed is reduced to 0, including any bonuses. Can be dragged by the grappling
        creature on its turn.
    - Restrained: Speed is 0, attack rolls and dexterity saving throws have disadvantage, and
        attacks against the creature have advantage.

    - Incapacitated: Can't take actions, bonus actions or reactions (can move and speak).
    - Stunned: Everything from Incpacitated, plus:
        - Can't move, and can only speak falteringly
        - Attack rolls against the creature have advantage
        - Automatically fail strength and dexterity saving throws
    - Paralyzed: Everything from Stunned, plus:
        - Can't speak at all
        - Any attack made within 5 ft that hits (melee or ranged) is an automatic critical hit
    - Unconscious: Everything from Paralyzed, plus:
        - Unaware of its surroundings
        - Creature drops whatever it's holding and falls prone
    - Petrified: Everything from Stunned, plus:
        - Can't speak at all
        - Unaware of its surroundings
        - The creature has resistance to all damage
        - The creature is immune to poison and disease

    """

    blinded = auto()
    charmed = auto()
    deafened = auto()
    frightened = auto()  # disadv on ability checks and attack rolls while source of fear is visible
    grappled = auto()
    incapacitated = auto()  # Can't take actions, bonus action or reaction
    invisible = auto()
    paralyzed = auto()  # Also incapacitated, can't move or speak, and attacks within 5 ft auto-crit
    petrified = auto()  # Also incapacitated, can't move or speak, and attacks within 5 ft auto-crit
    poisoned = auto()
    prone = auto()
    restrained = auto()
    stunned = auto()  # Also incapacitated, can't move & speak only falteringly
    unconscious = auto()  # Also incapacitated, prone, & can't move or speak
    # Not official conditions but useful to track
    dying = auto()
    dead = auto()


class DamageType(StrEnum):
    """Different types of damage that can be inflicted in the game."""

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
class Point:
    """Class to represent a point on a grid."""

    x: int
    y: int
    z: int = 0


class Size(IntEnum):
    """There are only 6 sizes in D&D!"""

    tiny = auto()
    small = auto()
    medium = auto()
    large = auto()
    huge = auto()
    gargantuan = auto()


### Creature stat things ###
class Ability(StrEnum):
    """Character abilities."""

    str = auto()
    dex = auto()
    con = auto()
    int = auto()
    wis = auto()
    cha = auto()


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


SKILL_MAPPING = {
    Skill.acrobatics: Ability.dex,
    Skill.animal_handling: Ability.wis,
    Skill.arcana: Ability.int,
    Skill.athletics: Ability.str,
    Skill.deception: Ability.cha,
    Skill.history: Ability.int,
    Skill.insight: Ability.wis,
    Skill.intimidation: Ability.cha,
    Skill.investigation: Ability.int,
    Skill.medicine: Ability.wis,
    Skill.nature: Ability.int,
    Skill.perception: Ability.wis,
    Skill.performance: Ability.cha,
    Skill.persuasion: Ability.cha,
    Skill.religion: Ability.int,
    Skill.sleight_of_hand: Ability.dex,
    Skill.stealth: Ability.dex,
    Skill.survival: Ability.wis,
}


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


class Sense(StrEnum):
    """Creature senses."""

    blindsight = auto()
    darkvision = auto()
    tremorsense = auto()
    truesight = auto()
