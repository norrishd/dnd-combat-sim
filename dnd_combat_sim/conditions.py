import abc
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Collection, Optional, Union


from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import Ability, Condition, Skill
from dnd_combat_sim.utils import get_distance


@dataclass
class TempCondition(abc.ABC):
    """Class to represent a temporary condition on a creature.

    Args:
        condition: Which condition is applied.
        creature: The creature affected by the condition.
        cause: The creature that caused/is maintaining the condition, e.g. the grappler.
        escape_dc: The DC to escape the condition, if applicable.
        escape_ability: One or more abilities that can be used to escape the condition.
        contested_ability: Where a contested check can break the condition, which abilities the
            maintainer can rolls with.
    """

    condition: Condition
    creature: Creature
    caused_by: Optional[Creature] = None
    escape_dc: Optional[int] = None
    escape_ability: Optional[Collection[Union[Ability, Skill]]] = None
    contested_by: Optional[list[Ability]] = None
    on_action: bool = False
    end_on_conditions: Optional[Collection[Condition]] = {
        Condition.dead,
        Condition.incapacitated,
    }


class Grappled(TempCondition):
    """Class to represent being grappled.

    Speed is reduced to 0, including any bonuses that apply.

    Ends if:
    - Creature uses its action to succeed on an acrobatics or athletics check contested by the
      grappler's athletics
    - Grappler is incapacitated/killed
    - Either creature gets hurled away, e.g. by thunderwave
    """

    def __init__(self, creature: Creature, caused_by: Creature) -> None:
        super().__init__(
            condition=Condition.grappled,
            creature=creature,
            caused_by=caused_by,
            escape_ability=[Skill.acrobatics, Skill.athletics],
            on_action=True,
            contested_by=[Skill.athletics],
        )

    def check_if_condition_ended(self):
        """Check whether the condition has ended for any reason."""
        if any(condition in self.caused_by.conditions for condition in self.end_on_conditions):
            return True

        return get_distance(self.creature, self.caused_by) > 5

    def try_to_end_condition(self) -> bool:
        """Attempt to end the condition."""
        escape_dc = self.caused_by.roll_check(self.contested_by)

        if self.creature.roll_check([Skill.acrobatics, Skill.athletics]) >= escape_dc:
            return True

        if any(
            condition in self.caused_by.conditions for condition in self.end_on_causer_condition
        ):
            self.creature.conditions.remove(self.condition)


class Grappling(TempCondition):
    """Class to represent grappling another creature.

    Speed is reduced to 0, including any bonuses that apply.

    Ends if:
    - Creature uses its action to succeed on an acrobatics or athletics check contested by the
      grappler's athletics
    - Grappler is incapacitated/killed
    - Either creature gets hurled away, e.g. by thunderwave
    """

    def __init__(self, creature: Creature, caused_by: Creature) -> None:
        super().__init__(
            condition=Condition.grappled,
            creature=creature,
            caused_by=caused_by,
            escape_ability=[Skill.acrobatics, Skill.athletics],
            on_action=True,
            contested_by=[Skill.athletics],
        )

    def check_if_condition_ended(self):
        """Check whether the condition has ended for any reason."""
        if any(condition in self.caused_by.conditions for condition in self.end_on_conditions):
            return True

        return get_distance(self.creature, self.caused_by) > 5


class PsuedopodGrappled(TempCondition):
    """Class to represent being grappled by a mimic's pseudopod."""

    def __init__(self, creature: Creature, caused_by: Creature) -> None:
        super().__init__(
            condition=Condition.grappled,
            creature=creature,
            caused_by=caused_by,
            escape_dc=13,
            escape_ability=[Skill.acrobatics, Skill.athletics],
            end_on_condition=[Condition.dead, Condition.incapacitated],
        )


TEMP_CONDITIONS = {
    "pseudopod_grappled": PsuedopodGrappled,
}
