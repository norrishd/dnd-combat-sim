import logging
import time
from typing import Union

from dnd_combat_sim.attack import AttackRoll, DamageOutcome
from dnd_combat_sim.creature import Condition, Creature
from dnd_combat_sim.trait import Battle, OnRollDamageTrait, OnTakeDamageTrait, Team, Trait
from dnd_combat_sim.traits import TRAITS, attach_traits

logger = logging.getLogger(__name__)


def log_and_pause(message: str, level: Union[int, str] = logging.INFO, sleep_time: float = 0.0):
    # print(message)
    logger.log(level, message)
    time.sleep(sleep_time)


class Encounter1v1:
    def __init__(self, creature1: Creature, creature2: Creature):
        self.creatures = [creature1, creature2]
        # Dict to track all conditions on creatures, and the creature that applied them
        self.battle = Battle([Team("team1", {creature1}), Team("team2", {creature2})])

    def run(self, to_the_death: bool = True) -> Creature:
        """Run an encounter between two creatures to the death, returning the winner."""
        # Reset creatures
        for creature in self.creatures:
            attach_traits(creature)

        # Roll initiative and determine order
        initiative = {creature: creature.roll_initiative() for creature in self.creatures}
        initiative = dict(sorted(initiative.items(), key=lambda item: item[1], reverse=True))
        init_str: str = "\n".join(
            f"{creature}: rolled {initiative}" for creature, initiative in initiative.items()
        )
        log_and_pause(f"Roll initiative:\n{init_str}", level=logging.DEBUG)

        self.battle.round = 1
        # Fight is on!
        while not any(Condition.dead in creature.conditions for creature in self.creatures):
            log_and_pause(f"\n* Round {self.battle.round} *", level=logging.DEBUG)
            for creature in initiative:
                enemy = self.creatures[1] if creature == self.creatures[0] else self.creatures[0]
                # Start of turn - reset counters, maybe roll death save or try to shake off a
                # temporary condition
                creature.start_turn()
                if Condition.dead in creature.conditions:
                    return enemy

                # Don't get a turn if have any of these conditions
                if any(
                    condition in creature.conditions
                    for condition in [
                        Condition.dead,
                        Condition.paralyzed,
                        Condition.petrified,
                        Condition.stunned,
                        Condition.unconscious,
                    ]
                ):
                    continue

                # Choose what to do
                action, bonus_action = creature.choose_action()

                # Make an attack
                if action == "attack":
                    self.resolve_attack(creature, enemy)
                    if (
                        Condition.dead in enemy.conditions
                        or Condition.dying in enemy.conditions
                        and not to_the_death
                    ):
                        return creature
                else:
                    log_and_pause(f"{creature.name} takes the {action} action", level=logging.DEBUG)

            log_and_pause(self.creatures)
            self.battle.round += 1  # Compare with target's AC

    def resolve_attack(self, attacker: Creature, target: Creature):
        """Resolve an attack from attacker to a target."""
        for _ in range(attacker.num_attacks):
            # 1. Attacker chooses which attack to use
            attack = attacker.choose_attack([target])

            # 2. Make attack roll
            attack_roll = attacker.roll_attack(attack)
            msg = f"{attacker.name} attacks {target.name} with {attack.name}: rolls {attack_roll}: "

            # 3. Check if attack hits (for now just considering AC, crits and crit fails)
            is_hit = self.check_if_hits(target, attack_roll)
            if not is_hit:
                log_and_pause(f"{msg}misses", level=logging.DEBUG)
                return

            # 4. If hits calculate damage, and check for trait modifiers, e.g. Martial advantage
            attack_damage = attacker.roll_damage(attack, crit=attack_roll.is_crit)
            for trait in attacker.traits:
                if isinstance(trait, OnRollDamageTrait):
                    damage_result = trait.on_roll_damage(
                        attacker,
                        damage_roll=attack_damage,
                        battle=self.battle,
                    )
            # 5. See if target modifies damage, e.g. from resistance or vulnerability
            modified_damage = target.modify_damage(attack_damage)
            msg += f"{'CRITS' if attack_roll.is_crit else 'hits'} for {modified_damage} damage."
            log_and_pause(msg, level=logging.DEBUG)

            if modified_damage.total > 0:
                # 6. Actually do the damage, then handle traits like undead fortitude
                damage_result = target.take_damage(attack_damage, crit=attack_roll.is_crit)
                for trait in target.traits:
                    if isinstance(trait, OnTakeDamageTrait):
                        damage_result = trait.on_take_damage(
                            target,
                            attack_damage,
                            damage_result,
                        )

            if damage_result == DamageOutcome.knocked_out:
                log_and_pause(f"{target.name} is down!", level=logging.DEBUG)
            elif damage_result == DamageOutcome.still_dying:
                log_and_pause(f"{target.name} is on death's door", level=logging.DEBUG)
            elif damage_result in {DamageOutcome.dead, DamageOutcome.instant_death}:
                log_and_pause(f"{target.name} is DEAD!", level=logging.DEBUG)
                return

    def check_if_hits(self, target: Creature, attack_roll: AttackRoll):
        """Resolve an attack from attacker to a target."""
        total = attack_roll.total

        # TODO resolve reactions like shield or parry
        # for trait in target.traits...
        # if target.has_reaction...
        if (total < target.ac and not attack_roll.is_crit) or attack_roll.rolled == 1:
            return False
        return True


class MultiEncounter1v1:
    def __init__(self, creature1: Creature, creature2: Creature, num_runs: int = 1000):
        self.creatures = [creature1, creature2]
        self.num_runs = num_runs
        self.wins = {creature.name: 0 for creature in self.creatures}

    def run(self, to_the_death: bool = True):
        """Run an encounter between two creatures to the death."""
        if 3 < self.num_runs <= 10:
            logging.getLogger().setLevel(logging.INFO)
        elif self.num_runs > 10:
            logging.getLogger().setLevel(logging.WARNING)

        for i in range(self.num_runs):
            log_and_pause(f"\n*** Encounter {i + 1} ***")
            encounter = Encounter1v1(self.creatures[0].spawn(), self.creatures[1].spawn())
            winner = encounter.run(to_the_death=to_the_death)
            self.wins[winner.name] += 1
            log_and_pause(f"Winner: {winner}")

        print("\n")
        for creature, wins in self.wins.items():
            print(f"{creature}: {wins} win(s)")
