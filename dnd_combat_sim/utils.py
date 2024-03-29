import logging
from pathlib import Path

import numpy as np
import pandas as pd

from dnd_combat_sim.rules import Position

# Suppress: FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated
# and will change in a future version. Call result.infer_objects(copy=False) instead.
pd.set_option("future.no_silent_downcasting", True)

logger = logging.getLogger(__name__)

ATTACKS_PATH = Path(__file__).parent / "content/attacks.csv"
MONSTERS_PATH = Path(__file__).parent / "content/monsters.csv"
WEAPONS_PATH = Path(__file__).parent / "content/weapons.csv"


def cr_to_float(cr: str) -> float:
    if "/" in cr:
        num, denom = cr.split("/")
        return int(num) / int(denom)
    return float(cr)


def get_distance(point1: Position, point2: Position) -> float:
    """Calculate the distance between two points."""
    return ((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2) ** 0.5


def load_attacks(*args, **kwargs):
    """Load all attacks from the attacks.csv file."""
    # Weapons
    weapons: pd.DataFrame = pd.read_csv(WEAPONS_PATH, *args, **kwargs)
    weapons["is_weapon"] = True
    # Natural attacks, e.g. claws
    attacks: pd.DataFrame = pd.read_csv(ATTACKS_PATH, *args, **kwargs)
    attacks["is_weapon"] = False
    attacks["type"] = "monster"

    attacks = pd.concat([attacks, weapons]).set_index("key")

    attacks = attacks.fillna(
        {
            "ammunition": False,
            "finesse": False,
            "heavy": False,
            "light": False,
            "loading": False,
            "reach": False,
            "thrown": False,
        }
    )
    attacks = attacks.fillna(np.nan).replace([np.nan], [None])

    return attacks


def load_monsters(*args, **kwargs) -> pd.DataFrame:
    """Load all monsters from the monsters.csv file."""

    monsters: pd.DataFrame = pd.read_csv(MONSTERS_PATH, *args, **kwargs).set_index("name")
    monsters = monsters.fillna(
        {
            "has_shield": False,
            "num_hands": 2,
            "speed": 30,
            "speed_hover": 0,
            "speed_fly": 0,
            "speed_swim": 0,
            "num_attacks": 1,
            "different_attacks": False,
            "versatile": True,
        },
    )

    int_cols = ["num_attacks", "num_hands", "speed", "speed_hover", "speed_fly", "speed_swim"]
    monsters[int_cols] = monsters[int_cols].astype(int)
    monsters = monsters.fillna(np.nan).replace([np.nan], [None])

    return monsters


ATTACKS = load_attacks()
MONSTERS = load_monsters()
