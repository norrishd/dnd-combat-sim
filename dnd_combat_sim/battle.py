from collections import defaultdict
from dnd_combat_sim.conditions import TempCondition
from dnd_combat_sim.creature import Creature


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
        self.temp_conditions: dict[Creature, set[TempCondition]] = defaultdict(set)

        self.round = 0

    def get_allies(self, creature: Creature) -> set[Creature]:
        creature_team = self.team_lookup[creature]
        return creature_team.creatures - {creature}

    def get_enemies(self, creature: Creature) -> set[Creature]:
        creature_team = self.team_lookup[creature]
        enemy_teams = set(self.teams) - {creature_team}
        return set(creature for team in enemy_teams for creature in team.creatures)
