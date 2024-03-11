from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Collection, Optional, Union


from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import Ability, Condition, Skill
from dnd_combat_sim.utils import get_distance


@dataclass
class TempCondition(abc.ABC):
    """Class to represent a temporary condition on a creature.

    Args:
        condition: Which condition is applied.
        affects: The creature affected by the condition, e.g. being grappled.
        causer: The creature that caused/is maintaining the condition, e.g. the grappler.
        escape_dc: The DC to escape the condition, if applicable.
        escape_ability: One or more abilities that can be used to escape the condition.
        contested_by: Where a contested check can end the condition, which ability the causer rolls.
        end_on_target_conditions: End this condition when the target has any of these conditions.
        end_on_causer_conditions: End this condition when the causer has any of these conditions.
    """

    condition: Condition
    target: Creature
    caused_by: Optional[Creature] = None
    escape_dc: Optional[int] = None
    escape_ability: Optional[Collection[Union[Ability, Skill]]] = None
    escape_modifiers: Optional[dict[str, Any]] = None
    contested_by: Optional[list[Ability]] = None
    on_action: bool = False
    end_on_target_conditions: Optional[Collection[Condition]] = (
        Condition.dead,
        Condition.incapacitated,
    )
    end_on_causer_conditions: Optional[Collection[Condition]] = ()

    def check_if_condition_ended(self, temp_conditions: dict[Creature, TempCondition]) -> bool:
        """Check whether the condition has ended for any reason, e.g. the target is dead."""
        conditions_on_target = temp_conditions[self.target]
        for condition in conditions_on_target:
            if condition in self.end_on_target_conditions:
                return True

        if self.caused_by is not None:
            causer_conditions = temp_conditions[self.caused_by]
            for condition in causer_conditions:
                if condition in self.end_on_causer_conditions:
                    return True

        return False


class Grappled(TempCondition):
    """Class to represent being grappled.

    Speed is reduced to 0, including any bonuses that apply.

    Ends if:
    - Creature uses its action to succeed on an acrobatics or athletics check contested by the
      grappler's athletics
    - Grappler is incapacitated/killed
    - Either creature gets hurled away, e.g. by thunderwave
    """

    def __init__(self, target: Creature, caused_by: Creature) -> None:
        super().__init__(
            condition=Condition.grappled,
            target=target,
            caused_by=caused_by,
            escape_ability=[Skill.acrobatics, Skill.athletics],
            contested_by=[Skill.athletics],
            on_action=True,
        )

    def check_if_condition_ended(self, temp_conditions: dict[Creature, TempCondition]) -> bool:
        """Check whether the condition has ended, either because of another condition on the
        grappler/grappled, e.g. incapacitated, or because they've somehow moved apart.
        """
        if super().check_if_condition_ended(temp_conditions):
            return True

        return get_distance(self.target, self.caused_by) > 5

    def try_to_end_condition(
        self,
        target_modifiers: Optional[dict[str, Any]] = None,
        caused_by_modifiers: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Attempt to end the condition as an action."""
        target_modifiers = target_modifiers or {}
        caused_by_modifiers = caused_by_modifiers or {}
        escape_dc = self.caused_by.roll_check(self.contested_by, **caused_by_modifiers)

        rolled = self.target.roll_check([Skill.acrobatics, Skill.athletics], **target_modifiers)
        if rolled >= escape_dc:
            return True


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
