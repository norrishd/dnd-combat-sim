"""
Teleport (Recharge 4-6). The dog magically teleports, along with any equipment it is wearing or carrying, up to 40 feet to an unoccupied space it can see. Before or after teleporting, the dog can make one bite attack.
"""


class Action:
    """Class to represent an allowed action."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"{self.name}: {self.description}"


class BonusAction:
    """Class to represent an allowed bonus action."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"{self.name}: {self.description}"


class TempBonusAction(BonusAction):
    """Class to represent a bonus action that can be used in a limited context.

    E.g. for one round only, as a result of a trait.
    """

    def __init__(self, name: str, description: str, duration: int):
        super().__init__(name, description)
        self.duration = duration

    def __repr__(self):
        return f"{self.name}: {self.description} (lasts {self.duration} turns)"
