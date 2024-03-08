import logging
import time
from typing import Union

from dnd_combat_sim.creature import Condition, Creature

logger = logging.getLogger("game")
logging.basicConfig(format="", level=logging.INFO)
logger.setLevel(logging.DEBUG)


def log_and_pause(message: str, level: Union[int, str] = logging.INFO, sleep_time: float = 0.1):
    # print(message)
    logger.log(level, message)
    time.sleep(sleep_time)


class Encounter1v1:
    def __init__(self, creature1: Creature, creature2: Creature):
        self.creatures = [creature1, creature2]

    def run(self, to_the_death: bool = True):
        """Run an encounter between two creatures to the death."""
        # Roll initiative and determine order
        initiative = {creature: creature.roll_initiative() for creature in self.creatures}
        initiative = dict(sorted(initiative.items(), key=lambda item: item[1], reverse=True))
        init_str: str = "\n".join(
            f"{creature}: rolled {initiative}" for creature, initiative in initiative.items()
        )
        log_and_pause(f"Roll initiative:\n{init_str}")

        round = 1
        while not any(Condition.dead in creature.conditions for creature in self.creatures):
            log_and_pause(f"\n*** Round {round} ***")
            for creature in initiative:
                # Choose what to do
                action, bonus_action = creature.choose_action()

                # Make an attack
                if action == "attack":
                    target = (
                        self.creatures[1] if creature == self.creatures[0] else self.creatures[0]
                    )
                    resolve_attack(creature, target)

                elif action == "death_saving_throw":
                    value, result, total_successes_and_failures = creature.roll_death_save()
                    log_and_pause(
                        f"{creature.name} rolled a {value} on their death saving throw: {result}\n"
                        f"{total_successes_and_failures}."
                    )
                    if result == "death":
                        if Condition.dead in target.conditions:
                            log_and_pause(f"{target.name} is DEAD!")
                            return

                else:
                    log_and_pause(f"{creature.name} takes the {action} action")

            round += 1  # Compare with target's AC


def resolve_attack(attacker: Creature, target: Creature):
    """Resolve an attack from attacker to a target."""
    # 1. Attacker chooses which attack to use
    attack = attacker.choose_attack()
    attack_total, attack_roll, modifiers, is_crit = attacker.roll_attack(attack)
    msg = (
        f"{attacker.name} attacks {target.name} with {attack.name}: "
        f"rolls {attack_total} ({attack_roll} + {modifiers}) - "
    )

    if attack_total < target.stats.ac and not is_crit:
        msg += "misses"
    else:
        damage = attacker.roll_damage(attack, crit=is_crit)
        damage_result = target.take_damage(damage, crit=is_crit)

        msg += f"{'CRITS' if is_crit else 'hits'} for {damage} damage."
        if damage_result == "alive":
            msg += f" {target.stats.hp}/{target.stats.max_hp} remaining"
        elif damage_result == "knocked out":
            msg += f"\n{target.name} is down!"
        elif damage_result == "dying":
            msg += f"\n{target.name} is on death's door"
        elif damage_result == "dead":
            msg += f"\n{target.name} is DEAD!"

    log_and_pause(msg)
