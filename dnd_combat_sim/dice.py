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


def roll(dice: Union[int, str], crit: bool = False, use_average: bool = False) -> int:
    """Roll one or more dice with a given number of sides, e.g. for damage or healing.

    Args:
        dice: Either an integer indicating the number of sides on the die (for a single die roll),
            or a string like "4d6" to indicate rolling 4x 6-sided dice and summing the result.
        crit: If True, double the number of dice rolled.
        use_average: If True, use the average value of the dice instead of rolling.
    """
    if isinstance(dice, str):
        num_dice, max_roll = map(int, dice.split("d"))
    else:
        num_dice = 1
        max_roll = dice

    if crit:
        num_dice *= 2

    if use_average:
        return (max_roll + 1) / 2 * num_dice

    return sum(random.randint(1, max_roll) for _ in range(num_dice))
