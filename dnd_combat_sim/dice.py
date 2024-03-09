import random


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


def roll(die: int = 8, use_average: bool = False) -> int:
    """Roll a die with a given number of sides, e.g. for damage or healing."""
    if use_average:
        return (die + 1) / 2

    return random.randint(1, die)
