import random


def roll_d20(advantage: bool = False, disadvantage: bool = False) -> int:
    if (advantage and disadvantage) or not (advantage and disadvantage):
        return random.randint(1, 20)
    if advantage:
        return max(random.randint(1, 20), random.randint(1, 20))

    return min(random.randint(1, 20), random.randint(1, 20))


def roll(dice: int = 8, use_average: bool = False) -> int:
    if use_average:
        return (dice + 1) / 2

    return random.randint(1, dice)
