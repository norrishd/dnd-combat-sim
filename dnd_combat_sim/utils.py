from pathlib import Path

import pandas as pd

MONSTERS_PATH = Path(__file__).parent / "monsters.csv"


def load_monsters(*args, **kwargs) -> pd.DataFrame:
    """Load all monsters from the monsters.csv file."""

    df: pd.DataFrame = pd.read_csv(MONSTERS_PATH, *args, **kwargs).set_index("name")
    df = df.fillna(
        {
            "has_shield": False,
            "speed": 30,
            "speed_hover": 0,
            "speed_fly": 0,
            "speed_swim": 0,
            "num_attacks": 1,
            "attacks_different": False,
            "versatile": True,
        }
    )
    df["num_attacks"] = df["num_attacks"].astype(int)

    return df


MONSTERS = load_monsters()
