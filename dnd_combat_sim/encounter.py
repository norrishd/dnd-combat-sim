import logging
from typing import Optional

from dnd_combat_sim.weapon import Weapon, AttackDamage, AttackRoll
from dnd_combat_sim.battle import Battle, Team
from dnd_combat_sim.conditions import TempCondition

from dnd_combat_sim.creature import Condition, Creature
from dnd_combat_sim.log import EncounterLogger
from dnd_combat_sim.rules import DamageOutcome
from dnd_combat_sim.traits.weapon_traits import (
    OnHitWeaponTrait,
    OnRollAttackWeaponTrait,
    attach_weapon_traits,
)
from dnd_combat_sim.traits.creature_traits import (
    OnRollAttackCreatureTrait,
    OnRollDamageTrait,
    OnTakeDamageTrait,
    attach_traits,
)
from dnd_combat_sim.utils import get_distance

logger = logging.getLogger(__name__)


class Encounter1v1:
    """Class to manage an encounter between two creatures."""

    def __init__(self, creature1: Creature, creature2: Creature):
        self.logger = EncounterLogger()

        self.battle = Battle([Team("team1", {creature1}), Team("team2", {creature2})])
        self.creatures = [creature1, creature2]
        for creature in self.creatures:
            attach_traits(creature)
            for attack in creature.attacks:
                attach_weapon_traits(attack)

        self.initiative = self.roll_initiative()

    def roll_initiative(self):
        """Roll initiative to determine combat order.

        # TODO: handle ties
        """
        initiative = {creature: creature.roll_initiative() for creature in self.creatures}
        initiative = dict(sorted(initiative.items(), key=lambda item: item[1], reverse=True))
        self.logger.log_roll_initiative(initiative)

        return initiative

    def take_turn(self, creature: Creature) -> None:
        """Take a turn for a creature."""
        enemy = self.creatures[1] if creature == self.creatures[0] else self.creatures[0]

        # Reset counters, roll a death save if at 0 HP and dying
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
            return None

        # Choose what to do
        action, bonus_action = creature.choose_action()

        # Make an attack
        if action == "attack":
            self.attack(creature, enemy)
            if Condition.dead in enemy.conditions or Condition.dying in enemy.conditions:
                # Enemy defeated; encounter over!
                return creature
        else:
            self.logger.log_choose_action(creature, action)

    def attack(self, attacker: Creature, target: Creature) -> None:
        """Resolve an attack from attacker to a target."""
        for _ in range(attacker.num_attacks):
            # 1. Attacker chooses which attack to use
            weapon = attacker.choose_weapon([target])

            # 2. Calculate any modifiers for the attack
            # Attack modifiers from a) creature traits, b) weapon traits, c_ temporary conditions
            attack_modifiers, auto_crit = self._get_attack_modifiers(weapon, attacker, target)
            # 3. Roll the attack
            attack_roll = attacker.roll_attack(weapon, **attack_modifiers)

            # 3. Check if attack hits, for now just considering AC, crits and crit fails
            if not self._check_if_hits(target, attack_roll):
                self.logger.log_miss(attacker, target, attack_roll)
                continue

            # 4. Calculate damage including attacker damage modifying traits, e.g. Martial advantage
            attack_damage = attacker.roll_damage(weapon, crit=attack_roll.is_crit or auto_crit)
            modified_damage = self._apply_damage_modifiers(attacker, attack_damage)

            # 5. Update damage from target resistance / vulnerability / immunity
            damage_taken = target.get_damage_taken(modified_damage)

            # 6. Actually do the damage, then resolve traits like undead fortitude
            damage_result = target.take_damage(damage_taken, crit=attack_roll.is_crit)
            damage_result = self._apply_post_damage_traits(target, attack_damage, damage_result)
            self.logger.log_hit(
                attacker, target, attack_roll, attack_damage, modified_damage, damage_taken
            )

            # Apply weapon traits which may deal extra damage or cause conditions
            conditions = self._apply_weapon_hit_traits(weapon, attacker, target)
            for condition in conditions:
                self.battle.add_condition(condition)
            self.logger.log_weapon_effects(conditions)

            self.logger.log_attack_outcome(damage_result, target)
            if damage_result in {DamageOutcome.dead, DamageOutcome.instant_death}:
                return

    def run(self, max_rounds: int = 10) -> Optional[Creature]:
        """Run an encounter between two creatures to the death, returning the winner."""
        self.battle.round = 1
        if self.battle.round > max_rounds:
            logger.debug("Battle is a stalemate!")
            return None

        # Fight is on!
        while not any(Condition.dead in creature.conditions for creature in self.creatures):
            self.logger.log_start_round(self.battle.round)
            for creature in self.initiative:
                self.take_turn(creature)

            self.logger.log_end_round(self.creatures)
            self.battle.round += 1  # Compare with target's AC

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

    def _get_attack_modifiers(
        self, attack: Weapon, attacker: Creature, target: Creature
    ) -> tuple[dict[str, bool], bool]:
        """Get modifiers to an attack role, i.e. advantage or disadvantage, and whether the damage
        roll should be an auto-crit upon hitting.

        These can come from multiple sources:
        - creature traits, e.g. Grappler when attacking a grappled target
        - weapon traits, e.g. Lance has disadvantage when attacking within 5ft
        - temporary conditions on either the attacker or target, e.g. attacking when invisible or
            being prone
        """
        auto_crit = False
        # Resolve modifiers from attack traits
        weapon_modifiers = {}
        for trait in attack.traits:
            if isinstance(trait, OnRollAttackWeaponTrait):
                modifier = trait.on_roll_attack(
                    attacker=attacker,
                    target=target,
                )
                if modifier:
                    weapon_modifiers[trait] = modifier
        # Resolve modifiers from creature traits
        attacker_modifiers = {}
        for trait in attacker.traits:
            if isinstance(trait, OnRollAttackCreatureTrait):
                modifier = trait.on_roll_attack(
                    attacker,
                    target=target,
                    battle=self.battle,
                )
                if modifier:
                    attacker_modifiers[trait] = modifier
        # Resolve modifiers from conditions on the attacker
        attacker_condition_modifiers = {}
        for condition in self.battle.temp_conditions[attacker]:
            if condition.condition in {Condition.invisible, Condition.unseen}:
                attacker_condition_modifiers[condition] = {"advantage": True}
            elif condition.condition in {Condition.prone, Condition.poisoned, Condition.frightened}:
                attacker_condition_modifiers[condition] = {"disadvantage": True}
            elif condition.condition == Condition.blinded and not attacker.senses:
                # TODO make this more robust
                attacker_condition_modifiers[condition] = {"disadvantage": True}
        # Resolve modifiers from conditions on the target
        target_condition_modifiers = {}
        for condition in self.battle.temp_conditions[target]:
            if condition.condition in {Condition.invisible, Condition.unseen}:
                target_condition_modifiers[condition] = {"disadvantage": True}
            elif condition.condition == Condition.blinded and not target.senses:
                target_condition_modifiers[condition] = {"advantage": True}
            elif condition.condition == Condition.prone:
                distance = get_distance(attacker.position, target.position)
                mod = {"advantage": True} if distance <= 5 else {"disadvantage": True}
                target_condition_modifiers[condition] = mod
            elif condition.condition in {
                Condition.restrained,
                Condition.stunned,
                Condition.petrified,
            }:
                target_condition_modifiers[condition] = {"advantage": True}
            elif condition.condition in {Condition.paralyzed, Condition.unconscious}:
                target_condition_modifiers[condition] = {"advantage": True}
                auto_crit = True

        self.logger.log_attack_modifiers(
            weapon_modifiers,
            attacker_modifiers,
            attacker_condition_modifiers,
            target_condition_modifiers,
        )

        modifiers = {}
        for modifier_set in [
            weapon_modifiers,
            attacker_modifiers,
            attacker_condition_modifiers,
            target_condition_modifiers,
        ]:
            for _trait, modifier in modifier_set.items():
                modifiers.update(modifier)
        return modifiers, auto_crit

    def _apply_damage_modifiers(
        self, attacker: Creature, attack_damage: AttackDamage
    ) -> AttackDamage:
        """Apply any attacker creature traits that modify damage dealt, e.g. Martial Advantage."""
        for trait in attacker.traits:
            if isinstance(trait, OnRollDamageTrait):
                attack_damage = trait.on_roll_damage(
                    attacker,
                    damage_roll=attack_damage,
                    battle=self.battle,
                )
        return attack_damage

    def _apply_post_damage_traits(
        self, target: Creature, attack_damage: AttackDamage, damage_result: DamageOutcome
    ) -> DamageOutcome:
        """Apply target traits that trigger after taking damage, e.g. undead fortitude."""
        for trait in target.traits:
            if isinstance(trait, OnTakeDamageTrait):
                damage_result = trait.on_take_damage(
                    target,
                    attack_damage,
                    damage_result,
                )
        return damage_result

    def _apply_weapon_hit_traits(
        self, attack: Weapon, attacker: Creature, target: Creature
    ) -> Optional[TempCondition]:
        """Apply any attack (weapon) traits that deal special effects on a hit."""
        conditions = []
        if attack.traits is not None:
            for trait in attack.traits:
                if isinstance(trait, OnHitWeaponTrait):
                    result = trait.on_attack_hit(attacker, target)
                    if result is not None:
                        conditions.append(result)
        return conditions


class MultiEncounter1v1:
    """Class to simulate running an encounter multiple times."""

    def __init__(self, creature1: Creature, creature2: Creature, num_runs: int = 1000):
        self.creatures = [creature1, creature2]
        self.num_runs = num_runs
        self.wins = {creature.name: 0 for creature in self.creatures}

    def run(self):
        """Run an encounter between two creatures to the death."""
        if 3 < self.num_runs <= 10:
            logging.getLogger().setLevel(logging.INFO)
        elif self.num_runs > 10:
            logging.getLogger().setLevel(logging.WARNING)

        for i in range(self.num_runs):
            encounter = Encounter1v1(self.creatures[0].spawn(), self.creatures[1].spawn())
            encounter.logger.log_encounter(i)
            winner = encounter.run()
            if winner is not None:
                self.wins[winner.name] += 1
                encounter.logger.log_winner(winner)

        if self.num_runs > 1:
            print("\n")
            for creature, wins in self.wins.items():
                print(f"{creature}: {wins} win(s)")
