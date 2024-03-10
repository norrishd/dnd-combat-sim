import abc

from dnd_combat_sim.attack import AttackDamage, DamageOutcome
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
        self.round = 0

    def get_allies(self, creature: Creature) -> set[Creature]:
        creature_team = self.team_lookup[creature]
        return creature_team.creatures - {creature}

    def get_enemies(self, creature: Creature) -> set[Creature]:
        creature_team = self.team_lookup[creature]
        enemy_teams = set(self.teams) - {creature_team}
        return set(creature for team in enemy_teams for creature in team.creatures)


class Trait(abc.ABC):
    """Base class for a special creature trait or ability."""


class OnRollAttackTrait(Trait):
    """ABC for traits that modify an attack roll."""

    @abc.abstractmethod
    def on_roll_attack(self, creature: Creature, target: Creature, battle: Battle):
        pass


class OnRollDamageTrait(Trait):
    """ABC for traits that modify a damage roll."""

    @abc.abstractmethod
    def on_roll_damage(self, creature: Creature, damage_roll: AttackDamage, battle: Battle):
        pass


class OnTakeDamageTrait(Trait):
    """ABC for traits that trigger after taking damage."""

    @abc.abstractmethod
    def on_take_damage(
        self, creature: Creature, damage: AttackDamage, damage_result: DamageOutcome
    ):
        pass
