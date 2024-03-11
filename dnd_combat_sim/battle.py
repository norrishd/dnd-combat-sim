from collections import defaultdict
from dnd_combat_sim import conditions
from dnd_combat_sim.conditions import TempCondition
from dnd_combat_sim.creature import Creature
from dnd_combat_sim.rules import Condition


class Team:
    def __init__(self, name: str, creatures: set[Creature]) -> None:
        self.name = name
        self.creatures = set(creatures)


class Battle:
    def __init__(self, teams: list[Team]) -> None:
        self.teams = teams
        self.team_lookup: dict[Creature, Team] = {}
        for team in teams:
            for creature in team.creatures:
                self.team_lookup[creature] = team
        self.temp_conditions: dict[Creature, list[TempCondition]] = defaultdict(list)

        self.round = 0

    def add_condition(self, condition: TempCondition) -> None:
        """Add a condition to a creature."""
        for temp_condition in self.temp_conditions[condition.target]:
            if (
                temp_condition.condition == condition.condition
                and temp_condition.caused_by == condition.caused_by
            ):
                raise ValueError(f"Trying to add a condition twice: {condition}")
        self.temp_conditions[condition.target].append(condition)

    def get_allies(self, creature: Creature) -> set[Creature]:
        """Get all allies of a creature."""
        creature_team = self.team_lookup[creature]
        return creature_team.creatures - {creature}

    def get_enemies(self, creature: Creature) -> set[Creature]:
        """Get all enemies of a creature."""
        creature_team = self.team_lookup[creature]
        enemy_teams = set(self.teams) - {creature_team}
        return set(creature for team in enemy_teams for creature in team.creatures)

    def has_condition(self, creature: Creature, condition: Condition) -> bool:
        """Check whether a creature has a given condition."""
        return any(temp_cond.condition == condition for temp_cond in self.temp_conditions[creature])

    def remove_condition(self, condition: TempCondition) -> None:
        """Remove a condition from a creature."""
        removed = False
        for temp_condition in self.temp_conditions[condition.target]:
            if temp_condition == condition:
                self.temp_conditions[condition.target].remove(temp_condition)
                removed = True
        if not removed:
            raise ValueError(f"Trying to remove a condition that doesn't exist: {condition}")
