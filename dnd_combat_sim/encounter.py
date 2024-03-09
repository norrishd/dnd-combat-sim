import logging
import time
from typing import Union

from dnd_combat_sim.creature import Condition, Creature

logger = logging.getLogger(__name__)


def log_and_pause(message: str, level: Union[int, str] = logging.INFO, sleep_time: float = 0.0):
    # print(message)
    logger.log(level, message)
    time.sleep(sleep_time)


class Encounter1v1:
    def __init__(self, creature1: Creature, creature2: Creature):
        self.creatures = [creature1, creature2]

    def run(self, to_the_death: bool = True) -> Creature:
        """Run an encounter between two creatures to the death, returning the winner."""
        # Reset creatures
        for i, creature in enumerate(self.creatures):
            self.creatures[i] = self.creatures[i].spawn()

        # Roll initiative and determine order
        initiative = {creature: creature.roll_initiative() for creature in self.creatures}
        initiative = dict(sorted(initiative.items(), key=lambda item: item[1], reverse=True))
        init_str: str = "\n".join(
            f"{creature}: rolled {initiative}" for creature, initiative in initiative.items()
        )
        log_and_pause(f"Roll initiative:\n{init_str}", level=logging.DEBUG)

        round = 1
        # Fight is on!
        while not any(Condition.dead in creature.conditions for creature in self.creatures):
            log_and_pause(f"\n* Round {round} *", level=logging.DEBUG)
            for creature in initiative:
                # Choose what to do
                action, bonus_action = creature.choose_action()

                # Make an attack
                if action == "attack":
                    target = (
                        self.creatures[1] if creature == self.creatures[0] else self.creatures[0]
                    )
                    self.resolve_attack(creature, target)
                    if (
                        Condition.dead in target.conditions
                        or Condition.dying in target.conditions
                        and not to_the_death
                    ):
                        return creature

                elif action == "death_saving_throw":
                    value, result, total_successes_and_failures = creature.roll_death_save()
                    log_and_pause(
                        f"{creature.name} rolled a {value} on their death saving throw: {result}\n"
                        f"{total_successes_and_failures}.",
                        level=logging.DEBUG,
                    )
                    if result == "death":
                        if Condition.dead in target.conditions:
                            log_and_pause(f"{target.name} is DEAD!", level=logging.DEBUG)
                            return creature

                else:
                    log_and_pause(f"{creature.name} takes the {action} action", level=logging.DEBUG)

            log_and_pause(self.creatures)
            round += 1  # Compare with target's AC

    def resolve_attack(self, attacker: Creature, target: Creature):
        """Resolve an attack from attacker to a target."""
        # 1. Attacker chooses which attack to use
        attacks = attacker.choose_attack([target])
        for attack in attacks:
            attack_total, attack_roll, modifiers, is_crit = attacker.roll_attack(attack)
            symbol = "+" if modifiers >= 0 else "-"
            msg = (
                f"{attacker.name} attacks {target.name} with {attack.name}: "
                f"rolls {attack_total} ({attack_roll} {symbol} {abs(modifiers)}): "
            )

            if (attack_total < target.ac and not is_crit) or attack_roll == 1:
                msg += "misses"
                log_and_pause(msg, level=logging.DEBUG)
            else:
                damage = attacker.roll_damage(attack, crit=is_crit)
                damage_result = target.take_damage(damage, crit=is_crit)

                msg += f"{'CRITS' if is_crit else 'hits'} for {damage} damage."
                if damage_result == "knocked out":
                    msg += f"\n{target.name} is down!"
                elif damage_result == "dying":
                    msg += f"\n{target.name} is on death's door"
                elif damage_result == "dead":
                    msg += f"\n{target.name} is DEAD!"

                log_and_pause(msg, level=logging.DEBUG)

                if damage_result == "dead":
                    return


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
