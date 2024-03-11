import logging
from typing import Optional

from dnd_combat_sim.attack import Attack, AttackDamage, AttackRoll
from dnd_combat_sim.battle import Battle, Team
from dnd_combat_sim.conditions import TempCondition

from dnd_combat_sim.creature import Condition, Creature
from dnd_combat_sim.rules import DamageOutcome
from dnd_combat_sim.traits.attack_traits import (
    OnHitAttackTrait,
    OnRollAttackAttackTrait,
    attach_attack_traits,
)
from dnd_combat_sim.traits.creature_traits import (
    OnRollAttackTrait,
    OnRollDamageTrait,
    OnTakeDamageTrait,
    attach_traits,
)
from dnd_combat_sim.utils import log_and_pause

logger = logging.getLogger(__name__)


class Encounter1v1:
    def __init__(self, creature1: Creature, creature2: Creature):
        self.creatures = [creature1, creature2]
        # Dict to track all conditions on creatures, and the creature that applied them
        self.battle = Battle([Team("team1", {creature1}), Team("team2", {creature2})])

    def run(self, to_the_death: bool = True, max_rounds: int = 10) -> Optional[Creature]:
        """Run an encounter between two creatures to the death, returning the winner."""
        # Reset creatures
        for creature in self.creatures:
            attach_traits(creature)
            for attack in creature.attacks:
                attach_attack_traits(attack)

        # Roll initiative and determine order
        initiative = {creature: creature.roll_initiative() for creature in self.creatures}
        initiative = dict(sorted(initiative.items(), key=lambda item: item[1], reverse=True))
        init_str: str = "\n".join(
            f"{creature}: rolled {initiative}" for creature, initiative in initiative.items()
        )
        log_and_pause(f"Roll initiative:\n{init_str}", level=logging.DEBUG)

        self.battle.round = 1
        if self.battle.round > max_rounds:
            logger.debug("Battle is a stalemate!")
            return None

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

    def resolve_attack(self, attacker: Creature, target: Creature) -> None:
        """Resolve an attack from attacker to a target."""
        for _ in range(attacker.num_attacks):
            # 1. Attacker chooses which attack to use
            attack = attacker.choose_attack([target])

            # 2. Make attack roll
            # Attack modifiers from a) creature traits, b) attack (e.g. weapon) traits
            modifiers, creature_traits_used = self._get_creature_attack_modifiers(attacker, target)
            attack_modifiers, attack_traits_used = self._get_attack_trait_modifiers(
                attack, attacker, target
            )
            modifiers.update(attack_modifiers)
            attack_roll = attacker.roll_attack(attack, **modifiers)
            if creature_traits_used:
                logger.debug(f"Triggered creature traits: {creature_traits_used}")
            if attack_traits_used:
                logger.debug(f"Triggered attack traits: {attack_traits_used}")

            msg = f"{attacker.name} attacks {target.name} with {attack.name}: rolls {attack_roll}: "

            # 3. Check if attack hits (for now just considering AC, crits and crit fails)
            is_hit = self._check_if_hits(target, attack_roll)
            if not is_hit:
                log_and_pause(f"{msg}misses", level=logging.DEBUG)
                continue

            # 4. If hit, calculate damage, and check for trait modifiers, e.g. Martial advantage
            attack_damage = attacker.roll_damage(attack, crit=attack_roll.is_crit)
            attack_damage = self._apply_attacker_trait_damage_modifiers(attacker, attack_damage)

            # 5. See if target modifies damage, e.g. from resistance or vulnerability
            modified_damage = target.modify_damage(attack_damage)
            msg += f"{'CRITS' if attack_roll.is_crit else 'hits'} for {modified_damage} damage"
            if attack_damage.total != attack_damage.total:
                msg += f" (modified from {attack_damage})"
            log_and_pause(msg, level=logging.DEBUG)

            if modified_damage.total > 0:
                # 6. Actually do the damage, then resolve traits like undead fortitude
                damage_result = target.take_damage(modified_damage, crit=attack_roll.is_crit)
                damage_result = self._apply_target_damage_modifiers(
                    target, attack_damage, damage_result
                )
            # Apply weapon traits which may deal more damage
            conditions = self._apply_weapon_on_hit_traits(attack, attacker, target)
            if conditions is not None:
                breakpoint()

            if damage_result == DamageOutcome.knocked_out:
                log_and_pause(f"{target.name} is down!", level=logging.DEBUG)
            elif damage_result == DamageOutcome.still_dying:
                log_and_pause(f"{target.name} is on death's door", level=logging.DEBUG)
            elif damage_result in {DamageOutcome.dead, DamageOutcome.instant_death}:
                log_and_pause(f"{target.name} is DEAD!", level=logging.DEBUG)
                return

    def _check_if_hits(self, target: Creature, attack_roll: AttackRoll):
        """Resolve an attack from attacker to a target."""
        total = attack_roll.total

        # TODO resolve reactions like shield or parry
        # Should this happen within Creature?
        # for trait in target.traits...
        # if target.has_reaction...
        if (total < target.ac and not attack_roll.is_crit) or attack_roll.rolled == 1:
            return False
        return True

    def _get_creature_attack_modifiers(
        self, attacker: Creature, target: Creature
    ) -> tuple[dict[str, bool], set[OnRollAttackTrait]]:
        """Get modifiers from creature traits that modify attack rolls."""
        modifiers = dict()
        traits_applied = set()
        for trait in attacker.traits:
            if isinstance(trait, OnRollAttackTrait):
                modifiers.update(
                    trait.on_roll_attack(
                        attacker,
                        target=target,
                        battle=self.battle,
                    )
                )
                traits_applied.add(trait)
        return modifiers, traits_applied

    def _get_attack_trait_modifiers(
        self, attack: Attack, attacker: Creature, target: Creature
    ) -> dict[str, bool]:
        modifiers = {}
        traits_applied = set()
        for trait in attack.traits:
            if isinstance(trait, OnRollAttackAttackTrait):
                modifiers.update(
                    trait.on_roll_attack(
                        attacker=attacker,
                        target=target,
                    )
                )
                traits_applied.add(trait)
        return modifiers, traits_applied

    def _apply_weapon_on_hit_traits(
        self, attack: Attack, attacker: Creature, target: Creature
    ) -> Optional[TempCondition]:
        """Apply any attack (weapon) traits that modify damage dealt."""
        if attack.traits is not None:
            for trait in attack.traits:
                if isinstance(trait, OnHitAttackTrait):
                    return trait.on_attack_hit(attacker, target)

    def _apply_attacker_trait_damage_modifiers(
        self, attacker: Creature, attack_damage: AttackDamage
    ) -> AttackDamage:
        """Apply any attacker creature traits that modify damage dealt."""
        for trait in attacker.traits:
            if isinstance(trait, OnRollDamageTrait):
                attack_damage = trait.on_roll_damage(
                    attacker,
                    damage_roll=attack_damage,
                    battle=self.battle,
                )
        return attack_damage

    def _apply_target_damage_modifiers(
        self, target: Creature, attack_damage: AttackDamage, damage_result: DamageOutcome
    ) -> DamageOutcome:
        """Apply target traits that modify the outcome of damage taken."""
        for trait in target.traits:
            if isinstance(trait, OnTakeDamageTrait):
                damage_result = trait.on_take_damage(
                    target,
                    attack_damage,
                    damage_result,
                )
        return damage_result


class MultiEncounter1v1:
    """Class to simulate running an encounter multiple times."""

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
            if winner is not None:
                self.wins[winner.name] += 1
                log_and_pause(f"Winner: {winner}")

        if self.num_runs > 1:
            print("\n")
            for creature, wins in self.wins.items():
                print(f"{creature}: {wins} win(s)")
