import random
from typing import Union


def roll_d20(advantage: bool = False, disadvantage: bool = False, lucky: bool = False) -> int:
    """Simulate rolling a d20, potentially applying special cases such as advantage or lucky."""
    result = random.randint(1, 20)

    if advantage:
        result = max(result, random.randint(1, 20))
    elif disadvantage:
        result = min(result, random.randint(1, 20))

    if lucky and result == 1:
        return roll_d20(advantage=advantage, disadvantage=disadvantage, lucky=False)

    return result


def roll(die: Union[int, str], use_average: bool = False) -> int:
    """Roll a die with a given number of sides, e.g. for damage or healing.

    Args:
        die: Either an integer indicating the number of sides on the die, or a string like "4d6" to
            indicate rolling 4x 6-sided die and summing the result.
    """
    if isinstance(die, str):
        num_dice, die = map(int, die.split("d"))
        return sum(roll(die, use_average) for _ in range(num_dice))

    if use_average:
        return (die + 1) / 2

    return random.randint(1, die)
