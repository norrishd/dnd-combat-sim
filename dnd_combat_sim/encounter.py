import logging
from typing import Optional

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
from dnd_combat_sim.weapon import Weapon, AttackDamage, AttackRoll

logger = logging.getLogger(__name__)


class Encounter1v1:
    """Class to manage an encounter between two creatures."""

    def __init__(self, creature1: Optional[Creature] = None, creature2: Optional[Creature] = None):
        self.logger = EncounterLogger()

        self.battle = None
        self.creatures: list[Optional[Creature]] = [creature1, creature2]
        if all(isinstance(creature, Creature) for creature in self.creatures):
            self.battle = Battle([Team("team1", {creature1}), Team("team2", {creature2})])

        # for creature in self.creatures:
        #     attach_traits(creature)
        #     for attack in creature.weapons:
        #         attach_weapon_traits(attack)

    def add_creature(self, creature: Creature) -> None:
        """Add a creature to the encounter."""
        if self.creatures[0] is None:
            self.creatures[0] = creature
        elif self.creatures[1] is None:
            self.creatures[1] = creature
        else:
            raise ValueError("Encounter is already full.")

        if all(isinstance(creature, Creature) for creature in self.creatures):
            self.battle = Battle(
                [Team("team1", {self.creatures[0]}), Team("team2", {self.creatures[1]})]
            )

    def run_encounter(self, max_rounds: int = 10) -> Optional[Creature]:
        """Run an encounter between two creatures to the death, returning the winner."""
        self.battle.round = 1
        self.initiative = self.roll_initiative()

        # Fight is on!
        while not any(Condition.dead in creature.conditions for creature in self.creatures):
            self.logger.log_start_round(self.battle.round)
            for creature in self.initiative:
                fight_won = self.take_turn(creature)
                if fight_won:
                    return creature

            self.logger.log_end_round(self.creatures)
            self.battle.round += 1
            if self.battle.round > max_rounds:
                logger.info("Battle is a stalemate!")
                return None

    def roll_initiative(self):
        """Roll initiative to determine combat order.

        # TODO: handle ties
        """
        initiative = {creature: creature.roll_initiative() for creature in self.creatures}
        initiative = dict(sorted(initiative.items(), key=lambda item: item[1], reverse=True))
        self.logger.log_roll_initiative(initiative)

        return initiative

    def take_turn(self, creature: Creature) -> bool:
        """Take a turn for a creature, returning a bool indicating whether it won the fight."""
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
        action, _bonus_action = creature.choose_action([enemy])

        # Make an attack
        if action == "attack":
            damage_outcome = self.attack(creature, enemy)
            if Condition.dead in enemy.conditions:
                return True
            return damage_outcome
        elif action == "dash":
            new_position, distance = creature.choose_movement([enemy])
            self.logger.log_movement(creature, enemy, new_position, distance, dash=True)
            creature.move(new_position)
        else:
            self.logger.log_choose_action(creature, action)
        return False

    def attack(self, attacker: Creature, target: Creature):
        """Resolve an attack from attacker to a target."""
        for _ in range(attacker.num_attacks):
            # TODO handle lizardfolk throwing spear for first attack and not being allowed to
            # repeat for second attack

            # 1. Optionally move to a new position
            new_position, distance = attacker.choose_movement([target])
            if new_position is not None:
                # TODO handle opportunity attacks
                # for target in targets: if not target.reaction_used_this_turn: ...
                self.logger.log_movement(attacker, target, new_position, distance)
                attacker.move(new_position)

            # 1. Choose who to attack, with which weapon, and optionally where to move first
            attack_plan = attacker.choose_attack([target])
            if attack_plan is None:
                logger.info(f"{attacker.name} has no valid attacks left.")
                break
            else:
                target, weapon, thrown = attack_plan

            # 3. Calculate any attack modifiers then roll the attack
            # Attack modifiers from a) creature traits, b) weapon traits, c) temporary conditions
            attack_modifiers, auto_crit = self._get_attack_modifiers(weapon, attacker, target)
            attack_roll = attacker.roll_attack(weapon, thrown=thrown, **attack_modifiers)
            self.logger.cache_attack(attacker, target, thrown, attack_modifiers, attack_roll)

            # 4. Check if attack hits, for now just considering AC, crits and crit fails
            if not self._check_if_hits(target, attack_roll):
                self.logger.log_miss(attack_roll)
                continue

            # 5. Calculate damage including attacker damage modifying traits
            attack_damage = attacker.roll_damage(weapon, crit=attack_roll.is_crit or auto_crit)
            # Damage modifiers so far: Martial advantage
            attack_damage, attack_traits_applied = self._apply_damage_modifiers(
                attacker, attack_damage
            )

            # 5. Update damage from target resistance / vulnerability / immunity
            damage_taken, resistances = target.get_damage_taken(attack_damage)

            # 6. Actually do the damage, then resolve traits like undead fortitude
            if damage_taken.total > 0:
                damage_outcome = target.take_damage(damage_taken, crit=attack_roll.is_crit)
                self.logger.log_hit(
                    target,
                    attack_roll,
                    attack_damage,
                    attack_traits_applied,
                    resistances,
                    damage_taken,
                    damage_outcome,
                )
                # So far: Undead fortitude
                damage_outcome = self._apply_post_damage_traits(
                    target, attack_damage, damage_outcome
                )
                self.logger.log_damage_outcome(target, damage_outcome)
                if damage_outcome in {DamageOutcome.dead, DamageOutcome.instant_death}:
                    return

            # Apply weapon traits which may deal extra damage or cause conditions
            # TODO are there any weapon effects that should be applied even if target is KOed/killed
            # by the damage?
            conditions = self._apply_weapon_hit_traits(weapon, attacker, target)
            for condition in conditions:
                self.battle.add_condition(condition)

            self.logger.log_weapon_effects(conditions)

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
    ) -> tuple[dict[str, str], bool]:
        """Get modifiers to an attack role, i.e. advantage or disadvantage, and whether the damage
        roll should be an auto-crit upon hitting.

        These can come from multiple sources:
        - creature traits, e.g. Grappler when attacking a grappled target
        - weapon traits, e.g. Lance has disadvantage when attacking within 5ft
        - temporary conditions on either the attacker or target, e.g. attacking when invisible or
            being prone

        Returns:
            A tuple of (modifiers, auto_crit: bool)
            `modifiers` is a dict of modifier to the/a cause.
            E.g. {"disadvantage": "long_range", "advantage": "attacking_invisible"}
        """
        auto_crit = False
        # Resolve modifiers from position
        position_modifiers = {}
        distance = get_distance(attacker.position, target.position)
        if distance <= 5:
            if not attack.melee:
                position_modifiers["ranged_in_melee"] = "disadvantage"
        elif attack.range is not None:
            if attack.range[0] < distance <= attack.range[1]:
                position_modifiers["long_range"] = "disadvantage"
            elif distance > attack.range[1]:
                raise ValueError(f"{attacker.name} is too far from {target.name} to attack")

        # Resolve modifiers from attack traits
        weapon_modifiers = {}
        for trait in attack.traits:
            if isinstance(trait, OnRollAttackWeaponTrait):
                reason, modifier = trait.on_roll_attack(
                    attacker=attacker,
                    target=target,
                )
                if modifier:
                    weapon_modifiers[reason] = modifier
        # Resolve modifiers from creature traits
        attacker_modifiers = {}
        for trait in attacker.traits:
            if isinstance(trait, OnRollAttackCreatureTrait):
                true_or_false = trait.on_roll_attack(
                    attacker,
                    target=target,
                    battle=self.battle,
                )
                if true_or_false:
                    attacker_modifiers[trait] = true_or_false
        # Resolve modifiers from conditions on the attacker
        attacker_condition_modifiers = {}
        for condition in self.battle.temp_conditions[attacker]:
            if condition.condition in {Condition.invisible, Condition.unseen}:
                attacker_condition_modifiers["attacking_from_unseen"] = "advantage"
            elif condition.condition in {Condition.prone, Condition.poisoned, Condition.frightened}:
                reason = f"attacking_{condition.condition.name}"
                attacker_condition_modifiers[reason] = "disadvantage"
            elif condition.condition == Condition.blinded and not attacker.senses:
                # TODO make this more robust
                attacker_condition_modifiers["attacking_blinded"] = "disadvantage"
        # Resolve modifiers from conditions on the target
        target_condition_modifiers = {}
        for condition in self.battle.temp_conditions[target]:
            if condition.condition in {Condition.invisible, Condition.unseen}:
                target_condition_modifiers["target_unseen"] = "disadvantage"
            elif condition.condition == Condition.blinded and not target.senses:
                target_condition_modifiers["target_blinded"] = "advantage"
            elif condition.condition == Condition.prone:
                distance = get_distance(attacker.position, target.position)
                mod = "advantage" if distance <= 5 else "disadvantage"
                target_condition_modifiers["target_prone"] = mod
            elif condition.condition in {
                Condition.restrained,
                Condition.stunned,
                Condition.petrified,
            }:
                reason = f"target_{condition.condition.name}"
                target_condition_modifiers[reason] = "advantage"
            elif condition.condition in {Condition.paralyzed, Condition.unconscious}:
                target_condition_modifiers[f"target_{condition.condition.name}"] = "advantage"
                # Auto crit on damage IF score a hit when rolling with advantage
                auto_crit = True

        self.logger.log_attack_modifiers(
            position_modifiers,
            weapon_modifiers,
            attacker_modifiers,
            attacker_condition_modifiers,
            target_condition_modifiers,
        )

        modifiers = {}
        for modifier_set in [
            position_modifiers,
            weapon_modifiers,
            attacker_modifiers,
            attacker_condition_modifiers,
            target_condition_modifiers,
        ]:
            for cause, modifier in modifier_set.items():
                modifiers[modifier] = cause
        return modifiers, auto_crit

    def _apply_damage_modifiers(
        self, attacker: Creature, attack_damage: AttackDamage
    ) -> tuple[AttackDamage, list[OnRollDamageTrait]]:
        """Apply any attacker traits that modify the AttackDamage, e.g. Martial Advantage."""
        traits_applied = []
        for trait in attacker.traits:
            if isinstance(trait, OnRollDamageTrait):
                attack_damage, applied = trait.on_roll_damage(
                    attacker,
                    damage_roll=attack_damage,
                    battle=self.battle,
                )
                if applied:
                    traits_applied.append(trait)
        return attack_damage, traits_applied

    def _apply_post_damage_traits(
        self, target: Creature, attack_damage: AttackDamage, damage_outcome: DamageOutcome
    ) -> DamageOutcome:
        """Apply target traits that trigger after taking damage, e.g. undead fortitude."""
        for trait in target.traits:
            if isinstance(trait, OnTakeDamageTrait):
                damage_outcome = trait.on_take_damage(
                    target,
                    attack_damage,
                    damage_outcome,
                )
        return damage_outcome

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
            logging.getLogger().setLevel(25)
        elif self.num_runs > 10:
            logging.getLogger().setLevel(logging.WARNING)

        for i in range(self.num_runs):
            encounter = Encounter1v1(self.creatures[0].spawn(), self.creatures[1].spawn())
            encounter.logger.log_encounter(i)
            winner = encounter.run_encounter()
            if winner is not None:
                self.wins[winner.name] += 1
                encounter.logger.log_winner(winner)
            else:
                if "Stalemate" not in self.wins:
                    self.wins["Stalemate"] = 1
                else:
                    self.wins["Stalemate"] += 1

        if self.num_runs > 1:
            print("\n")
            for creature, wins in self.wins.items():
                print(f"{creature}: {wins} {'win(s)' if creature != 'Stalemate' else ''}")
