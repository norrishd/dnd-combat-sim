"""Module to define the Creature class and related methods."""

from __future__ import annotations

import logging
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import Collection, List, Optional, Sequence, Union

from dnd_combat_sim.weapon import Weapon, AttackDamage, AttackRoll, DamageType
from dnd_combat_sim.dice import roll, roll_d20
from dnd_combat_sim.rules import (
    Ability,
    Condition,
    CreatureType,
    DamageOutcome,
    Point,
    Sense,
    Size,
    Skill,
    SKILL_MAPPING,
)
from dnd_combat_sim.utils import MONSTERS, get_distance

logger = logging.getLogger(__name__)


@dataclass
class Abilities:
    """Class to store ability scores and modifiers."""

    str: int
    dex: int
    con: int
    int: int
    wis: int
    cha: int

    def get_modifier(self, ability: Ability) -> int:
        """Get the modifier for an ability score."""
        score = getattr(self, ability.name)
        return (score - 10) // 2


class Creature:
    """Class to store all state for a creature."""

    def __init__(
        self,
        name: str,
        ac: int,
        hp: Union[str, int],  # e.g. '5d6' or 16
        abilities: Union[Abilities, list[int]] = Abilities(10, 10, 10, 10, 10, 10),
        actions: Optional[Sequence[str]] = None,  # Optional non-attack actions, e.g. teleport
        attack_bonus: Optional[int] = None,  # Overrides proficiency + mods if provided
        attacks: Sequence[Union[Weapon, str]] = None,
        cond_immunities: Optional[Collection[Condition]] = None,
        cr: Optional[float] = None,
        creature_subtype: Optional[str] = None,  # No mechanical meaning?
        creature_type: Optional[CreatureType] = None,
        different_attacks: bool = True,
        has_shield: bool = False,  # Relevant for using two-handed weapons
        immunities: Optional[Collection[DamageType]] = None,
        make_death_saves: bool = False,
        num_attacks: int = 1,
        num_hands: int = 2,
        position: Point = Point(0, 0),
        proficiency: Optional[int] = None,  # Can be inferred from CR
        resistances: Optional[Collection[DamageType]] = None,
        save_proficiencies: Optional[Collection[Union[Ability, str]]] = None,
        senses: Optional[Union[Collection[Sense], dict[Sense, int]]] = None,
        size: Optional[Union[Size, str]] = None,  # Can infer from hit die type if not provided
        skill_proficiencies: Optional[Collection[Skill]] = None,
        skill_expertises: Optional[Collection[Skill]] = None,
        speed: int = 30,
        speed_fly: int = 0,
        speed_hover: int = 0,
        speed_swim: int = 0,
        # spell_slots: dict[int, int] = None,
        # spells: list[str] = None,
        traits: List[str] = None,
        vulnerabilities: Optional[Collection[DamageType]] = None,
    ) -> None:
        """Create a creature.

        Args:
            name: What to call the creature.
            ac: Armour class.
            hp: Max hit points, either absolute int or dice to roll, e.g. "5d6", for 5x 6-sided die.
            abilities: Ability scores, in order STR, DEX, CON, INT, WIS, CHA.
            attack_bonus: Override for proficiency bonus + attack modifier for all attacks.
            attacks: List of attacks the creature can make.
            cond_immunities: Conditions the creature is immune to.
            cr: Challenge rating. Used to infer proficiency if not provided.
            creature_subtype: E.g. "goblinoid", "demon", "shapeshifter".
            creature_type: E.g. "humanoid", "fiend", "undead".
            different_attacks: Whether a creature must use different attacks on a given turn when
                `num_attacks` > 1.
            has_shield: Whether the creature has a shield equipped. Relevant for two-handed attacks.
            immunities: Damage types the creature is immune to.
            make_death_saves: Whether the creature should make death saving throws when reduced to
                0 HP (e.g. player characters) or die outright (e.g. standard monsters).
            num_attacks: Number of attacks the creature can make on its turn.
            num_hands: Number of hands the creature has. Relevant for two-handed attacks.
            proficiency: Proficiency bonus to apply for attacks, saving throws etc. Can be inferred
                from CR if not provided.
            resistances: Damage types the creature is resistant to.
            save_proficiencies: Ability saving throws for which the creature is proficient.
            senses: Senses the creature has, e.g. darkvision, blindsight, tremorsense. Not currently
                used for anything.
            size: Size of the creature, e.g. "small", "medium", "large". If not provided, can be
                inferred from `hp` if provided as a string.
            skill_proficiencies: Skills the creature is proficient in.
            skill_expertises: Skills the creature has expertise in (i.e. double proficiency).
            speed: Movement speed in feet.
            speed_fly: Flying speed in feet.
            speed_hover: Hovering speed in feet.
            speed_swim: Swimming speed in feet.
            traits: List of keys for traits the creature has, e.g. undead_fortitude. See `TRAITS` in
                _traits.py_.
            vulnerabilities: Damage types the creature is vulnerable to.
        """
        self.name = name
        self.ac = ac
        self.abilities = Abilities(*abilities) if isinstance(abilities, list) else abilities
        self.actions = actions
        self.cr = cr
        # Parse hit points
        if isinstance(hp, str):
            self.num_hit_die, self.hit_die = map(int, hp.split("d"))  # E.g. "5d6" -> (5, 6)
            self.hp = self.max_hp = self._roll_hit_points()
        else:
            self.num_hit_die, self.hit_die = None, None
            self.hp = self.max_hp = hp
        # Parse size
        if size is None and self.hit_die is not None:
            size = {
                6: Size.small,
                8: Size.medium,
                10: Size.large,
                12: Size.huge,
                20: Size.gargantuan,
            }[self.hit_die]
        elif isinstance(size, str):
            size = Size[size]
        self.size = size
        # Parse proficiency
        if proficiency is None:
            if cr is not None:
                # DMG maps challenge rating to suggested proficiency bonus
                proficiency = max(cr - 1, 0) // 4 + 2
            else:
                raise ValueError("Must provide at least one of ['proficiency', 'cr']")

        self.attack_bonus = attack_bonus
        attacks = attacks or []
        self.weapons = [
            Weapon.init(attack, size=self.size) if not isinstance(attack, Weapon) else attack
            for attack in attacks
        ]
        self._melee_weapons = [attack for attack in self.weapons if attack.melee]
        self._ranged_weapons = [attack for attack in self.weapons if not attack.melee]
        self.weapons.append(Weapon.init("unarmed_strike"))
        self.cond_immunities = cond_immunities or set()
        self.creature_subtype = creature_subtype
        self.creature_type = creature_type
        self.different_attacks = different_attacks
        self.has_shield = has_shield
        self.immunities = immunities or set()
        self.make_death_saves = make_death_saves
        self.num_attacks = num_attacks
        self.num_hands = num_hands
        self.position = position
        self.proficiency = proficiency
        self.resistances = resistances or set()
        self.save_proficiencies = {
            Ability[save] if isinstance(save, str) else save
            for save in (save_proficiencies or [])
            if save
        }
        self.senses = senses or set()
        self.skill_proficiencies = {
            Skill[skill] if isinstance(skill, str) else skill
            for skill in (skill_proficiencies or [])
            if skill
        }
        self.skill_expertises = {
            Skill[skill] if isinstance(skill, str) else skill
            for skill in (skill_expertises or [])
            if skill
        }
        self.speed = speed
        self.speed_fly = speed_fly
        self.speed_hover = speed_hover
        self.speed_swim = speed_swim
        # self.spell_slots_total = spell_slots or {}
        # self.spell_slots = spell_slots_total.copy() if spell_slots
        self.traits = traits or []
        self.vulnerabilities = vulnerabilities or set()

        # Combat stuff
        self.remaining_movement: int = speed
        self.attack_used: bool = False
        self.weapons_used_this_turn: set[str] = set()
        self.bonus_action_used: bool = False
        self.reaction_used: bool = False
        self.conditions: set[Condition] = set()
        self.temp_hp: int = 0
        self.death_saves: dict[str, int] = {"successes": 0, "failures": 0}

    @classmethod
    def init(
        cls,
        monster: str,
        name: Optional[str] = None,
        make_death_saves: bool = False,
        start_x: int = 0,
    ) -> Creature:
        """Create a creature from a monster template."""
        stats = MONSTERS.loc[monster].to_dict()

        # Parse fields that need it
        stats["name"] = monster.title() if name is None else name.title()
        stats["abilities"] = [stats.pop(ability) for ability in Ability.__members__]
        size = Size[stats["size"]]
        stats["size"] = size
        stats["attacks"] = [
            Weapon.init(attack, size=size) for attack in (stats["attacks"] or "").split(",")
        ]
        stats["creature_type"] = CreatureType[stats["creature_type"]]
        stats["make_death_saves"] = make_death_saves
        stats["position"] = Point(start_x, 0)
        if stats["senses"]:
            stats["senses"] = [Sense[sense] for sense in stats["senses"].split(",")]

        for key in [
            "cond_immunities",
            "immunities",
            "resistances",
            "save_proficiencies",
            "skill_proficiencies",
            "skill_expertises",
            "traits",
            "vulnerabilities",
        ]:
            stats[key] = stats[key].split(",") if stats[key] else None

        return cls(**stats)

    @property
    def best_melee_weapon(self):
        """Reserved weapon for melee attacks that shouldn't be thrown."""
        best_melee_damage = 0
        best_melee_weapon = None
        for weapon, expected_damage in self._get_expected_damages(self._melee_weapons):
            if expected_damage > best_melee_damage:
                best_melee_damage = expected_damage
                best_melee_weapon = weapon
            elif expected_damage == best_melee_damage:
                # If find an equally good weapon that also has reach, use that
                if weapon.reach:
                    best_melee_weapon = weapon
                # Or if equally good and can't be thrown, use that
                elif best_melee_weapon.thrown and not weapon.thrown:
                    best_melee_weapon = weapon
        return best_melee_weapon

    def choose_action(self, targets: list[Creature]) -> tuple[str, Optional[str]]:
        """Choose an action and bonus action for the turn.

        For now just attack if possible, else dash toward nearest enemy.
        """
        # available_actions = ["dash", "disengage", "dodge", "hide", "search"]
        _closest_targets, distance = self._get_closest_enemies(targets)

        if self._can_attack(distance):
            logger.debug(f"{self.name} choosing to attack")
            available_actions = ["attack"]
        else:
            logger.debug(f"{self.name} can't attack, dashing")
            self.remaining_movement += self.speed
            available_actions = ["dash"]

        action = random.choice(available_actions)
        bonus_action = random.choice([None])

        return action, bonus_action

    def choose_attack(self, targets: list[Creature]) -> tuple[Creature, Weapon, bool]:
        """Choose a target to attack, a weapon to use, and whether to throw it (if melee)."""
        target = random.choice(targets)
        distance = get_distance(self.position, target.position)

        attack_options = self._get_attack_options(distance=distance)
        melee_options = [opt for opt in attack_options if opt[0].range is None]
        ranged_options = [opt for opt in attack_options if opt[0].range is not None]

        # If in melee range, only use ranged weapons that trump any melee option
        if distance <= 5:
            best_melee_damage = max(melee[1] for melee in melee_options)
            ranged_options = [opt for opt in ranged_options if opt[1] > best_melee_damage]

        attack_options = melee_options + ranged_options
        try:
            expected_damages = [attack[1] for attack in attack_options]
        except IndexError:
            breakpoint()
        weapon_choice = random.choices(melee_options + ranged_options, weights=expected_damages)[0]

        return target, weapon_choice[0], weapon_choice[2]

    def choose_movement(self, enemies: list[Creature]) -> Optional[Point]:
        """Plan where to move before taking an attack action.

        Return a new Point or None to indicate no movement.

        Uses a strategy that aims to fulfil the following principles:
        1. Always attack the nearest enemy
        2. Don't take opportunity attacks
        3. Prioritise doing the most expected damage
        4. Always be prepared for melee combat
        """
        if self.remaining_movement == 0:
            logger.debug("No more movement, staying")
            return None

        # Choose closest target to attack (P1)
        enemies, distance = self._get_closest_enemies(enemies)
        if distance <= 5:  # If in melee range of any enemy, don't move (P1, P2)
            logger.debug(f"Already in melee range ({distance}), staying")
            return None

        ideal_distance = None
        if distance <= 10:
            in_enemy_reach = any(weapon.reach for enemy in enemies for weapon in enemy.weapons)
            if in_enemy_reach:
                # Decide whether to close in for 5ft melee or attack from 10 ft
                attack_options_5_ft = self._get_attack_options(10)
                attack_options_10_ft = self._get_attack_options(10)
                best_damage_5_ft = max(attack[1] for attack in attack_options_5_ft)
                best_damage_10_ft = max(attack[1] for attack in attack_options_10_ft)
                if best_damage_10_ft > best_damage_5_ft:
                    logger.debug(
                        f"Ideal distance 10 ft, {best_damage_10_ft=} vs {best_damage_5_ft=}"
                    )
                    ideal_distance = 10
                else:
                    logger.debug(
                        f"Ideal distance 5 ft, {best_damage_10_ft=} vs {best_damage_5_ft=}"
                    )
                    ideal_distance = 5

        if ideal_distance is None:
            # If not in enemy melee range, figure out the ideal distance to be (P1, P3)
            # Just move in the x direction for now
            ideal_distance = self._get_ideal_distance()

        target = random.choice(enemies)
        # E.g. currently 30 ft away, want to be 5 ft away -> move 25 ft closer
        ideal_movement_toward_enemy = distance - ideal_distance
        movement_toward_enemy = min(ideal_movement_toward_enemy, self.remaining_movement)
        if target.position.x < self.position.x:
            movement_toward_enemy = -movement_toward_enemy

        logger.debug(f"Moving {movement_toward_enemy} ft toward {target.name}")
        return Point(self.position.x + movement_toward_enemy, self.position.y)

    def get_damage_taken(self, attack_damage: AttackDamage) -> AttackDamage:
        """Apply immunities, resistances and vulnerabilities to update attack damage."""
        attack_damage = deepcopy(attack_damage)
        for dtype in attack_damage.damages:
            if dtype in self.immunities:
                attack_damage.damages.pop(dtype)
            elif dtype in self.vulnerabilities:
                attack_damage.damages[dtype] *= 2
            elif dtype in self.resistances:
                attack_damage.damages[dtype] //= 2

        return attack_damage

    def heal(self, amount: int, wake_up: bool = True) -> None:
        """Recover hit points."""
        self.hp = min(self.hp + amount, self.max_hp)
        self.conditions.discard(Condition.dead)
        self.conditions.discard(Condition.dying)
        if wake_up:
            self.conditions.discard(Condition.unconscious)

    def move(self, new_position: Point) -> None:
        """Move the creature a given location."""
        from_pos = self.position
        self.position = new_position
        logger.debug(f"{self.name} moved from {from_pos} to {new_position}")

    def roll_attack(
        self,
        weapon: Weapon,
        thrown: bool = False,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> AttackRoll:
        """Make an attack roll, returning an AttackRoll describing it."""
        self.attack_used = True
        self.weapons_used_this_turn.add(weapon.name)
        # If firing a projectile or throwing the weapon, decrease the count
        if not weapon.melee or thrown:
            weapon.quantity -= 1
            if weapon.quantity == 0:
                span = "ammo for" if weapon.ammunition else ""
                logger.debug(f"{self.name} using up last {span} {weapon.name}!")

        # Roll to attack
        rolled = roll_d20(advantage=advantage, disadvantage=disadvantage)

        if self.attack_bonus is not None:
            modifier = self.attack_bonus
        else:
            modifier = self._get_attack_modifier(weapon)
            modifier += self.proficiency if weapon.proficient else 0

        return AttackRoll(rolled, modifier, self._is_crit(rolled), weapon)

    def roll_check(
        self,
        ability_or_skill: Optional[Collection[Union[Ability, Skill]]] = None,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> int:
        """Roll a skill or ability check."""
        rolled = roll_d20(advantage=advantage, disadvantage=disadvantage)

        modifier = 0
        if ability_or_skill is not None:
            modifier = self._get_modifier(ability_or_skill)

        return rolled + modifier

    def roll_damage(self, attack: Weapon, crit: bool = False) -> AttackDamage:
        """Roll damage for an attack that has hit."""
        # Use two-handed damage if have a spare hand
        damage_modifier = self._get_attack_modifier(attack)

        damage = attack.roll_damage(
            two_handed=self._get_num_free_hands() >= 2,
            crit=crit,
            damage_modifier=damage_modifier,
            use_average=False,
        )
        return damage

    def roll_death_save(self) -> tuple[int, str]:
        """Roll a death saving throw.

        Return the roll and result."""
        death_save = roll_d20()

        if death_save == 1:
            result = "critical failure"
            self.death_saves["failures"] += 2
        elif 2 <= death_save <= 9:
            result = "failure"
            self.death_saves["failures"] += 1
        elif 10 <= death_save <= 19:
            result = "success"
            self.death_saves["successes"] += 1
            if self.death_saves["successes"] == 3:
                result = "stabilised"
                self.conditions.add(Condition.stable)
                self._reset_death_saves()
        elif death_save == 20:
            result = "critical success"
            self.heal(1, wake_up=True)
            self._reset_death_saves()

        if self.death_saves["failures"] >= 3:
            self._die()
            result = "death"

        return death_save, result

    def roll_initiative(self):
        """Roll initiative for the creature."""
        return roll_d20() + self.abilities.get_modifier(Ability.dex)

    def roll_saving_throw(
        self, ability: Ability, advantage: bool = False, disadvantage: bool = False
    ) -> int:
        """Roll a saving throw for a given ability."""

        save = roll_d20(advantage=advantage, disadvantage=disadvantage)
        modifier = self.abilities.get_modifier(ability)
        if ability in self.save_proficiencies:
            modifier += self.proficiency

        return save + modifier

    def spawn(self, name: Optional[str] = None) -> Creature:
        """Create a new copy of this creature with the same stas but statuses reset."""
        new_creature = deepcopy(self)
        if name is not None:
            new_creature.name = name

        # Roll new HP; reset spell slots, conditions and death saves
        if self.num_hit_die is not None:
            new_creature.hp = new_creature.max_hp = self._roll_hit_points()
        else:
            new_creature.hp = new_creature.max_hp
        new_creature.start_turn()
        # new_creature.spell_slots = self.total_spell_slots.copy()
        new_creature.conditions = set()
        new_creature.death_saves = {"successes": 0, "failures": 0}

        return new_creature

    def start_turn(self) -> None:
        """Indicate the start of a new turn, reset transient state."""
        self.remaining_movement = self.speed
        self.attack_used = False
        self.weapons_used_this_turn: set[str] = set()
        self.bonus_action_used = False
        self.reaction_used = False

        if Condition.dying in self.conditions:
            value, result = self.roll_death_save()
            logger.debug(
                f"{self.name} rolled a {value} on their death saving throw: {result}\n"
                f"{self.death_saves}."
            )
            if result == "death":
                logger.debug(f"{self.name} is DEAD!")

    def take_damage(
        self,
        damage: AttackDamage,
        crit: bool = False,
    ) -> DamageOutcome:
        """Take damage from a hit and return the outcome of the damage."""
        total_damage = damage.total

        damage_taken = min(total_damage, self.hp)
        excess_damage = total_damage - damage_taken
        self.hp -= damage_taken

        # Check for instant death
        if excess_damage > self.max_hp:
            self._die()
            return DamageOutcome.instant_death

        if self.hp > 0:
            return DamageOutcome.alive

        if Condition.dying in self.conditions:
            # Already making death saving throws, get failure(s) instead of damage
            self.death_saves["failures"] += 1 if not crit else 2
            if self.death_saves["failures"] >= 3:
                return self._die()
            return DamageOutcome.still_dying

        if self.make_death_saves:
            self.conditions.update([Condition.unconscious, Condition.dying])
            return DamageOutcome.knocked_out
        return self._die()

    ### Private methods ###
    def _can_attack(self, distance: float) -> bool:
        """Check whether it's possible to attack a target at a given distance this turn."""
        # Check whether can move into melee attack range
        min_range = distance - self.remaining_movement
        usable_weapons = self._usable_weapons(self.weapons, distance_from_target=min_range)
        if usable_weapons:
            logger.debug(f"{self.name} can use {usable_weapons} at {distance} ft")
        else:
            logger.debug(f"{self.name} has no usable weapons at {distance} ft")

        return len(usable_weapons) > 0

    def _can_grapple(self, target: Creature) -> bool:
        """Check if the creature can grapple a target.

        Must have at least 1 free hand, be within reach, and target can't be more than 1 size
        larger.
        """
        return not any(
            ((target.size - self.size) > 1),
            (self._get_num_free_hands() < 1),
            (get_distance(self.position, target.position) > 5),
        )

    def _die(self) -> str:
        self.conditions.add(Condition.dead)
        self.conditions.discard(Condition.dying)
        self.conditions.discard(Condition.unconscious)
        # logger.info(f"{self.name} died")

        return DamageOutcome.dead

    def _get_attack_modifier(self, attack: Weapon) -> int:
        """Get an attack modifier:

        - strength for melee attacks
          - or dexterity for finesse weapons (whichever is higher)
        - dexterity for ranged attacks
          - or strength for thrown weapons, or either for thrown finesse weapons
        """
        if attack.finesse:
            return self._get_modifier([Ability.str, Ability.dex])
        if attack.melee:
            return self._get_modifier(Ability.str)

        return self._get_modifier(Ability.dex)

    def _get_attack_options(
        self, distance: Optional[int] = None
    ) -> list[tuple[Weapon, float, bool]]:
        """Get a list of available weapon attacks that can be made.

        If distance is not None, only include attacks that can be made at that distance, and apply
        a penalty for disadvantage, e.g. using a ranged weapon for melee or firing at long range.

        Return a list of tuples of (weapon, expected damage, whether requires ammo/throwing).
        """
        attack_options = []

        # Expected damage for all weapons, assume no disadvantage
        if distance is None:
            for weapon, expected_damage in self._get_expected_damages(self.weapons):
                attack_options.append((weapon, expected_damage, False))
                logger.debug(
                    f"{self.name} can use {weapon.name} for {expected_damage} average damage"
                )
            return attack_options

        # Expected damage assuming melee - ranged attacks made with disadvantage
        if distance == 5:
            for weapon, expected_damage in self._get_expected_damages(self.weapons):
                if not weapon.melee:
                    expected_damage /= 2
                attack_options.append((weapon, expected_damage, False))
                logger.debug(
                    f"{self.name} can use {weapon.name} for {expected_damage} average melee damage"
                )
            return attack_options

        # Identify a best melee weapon to safekeeping
        best_melee_damage = 0
        best_melee_weapon = None
        reach_weapons = []
        for weapon, expected_damage in self._get_expected_damages(self._melee_weapons):
            if distance <= 10 and weapon.reach:
                attack_options.append((weapon, expected_damage, False))
                logger.debug(
                    f"{self.name} can use {weapon.name} for {expected_damage} average reach damage"
                )
                reach_weapons.append(weapon)
            if expected_damage > best_melee_damage:
                best_melee_damage = expected_damage
                best_melee_weapon = weapon
            elif expected_damage == best_melee_damage:
                # If find an equally good weapon that also has reach or can't be thrown, keep it
                if weapon.reach:
                    best_melee_weapon = weapon
                elif not weapon.thrown:
                    best_melee_weapon = weapon

        # Add all valid ranged/thrown attacks
        for weapon, expected_damage in self._get_expected_damages(self.weapons, distance=distance):
            # Don't throw away best melee weapon, or throw if can use reach
            if weapon == best_melee_weapon or weapon in reach_weapons:
                logger.debug(f"Skipping {weapon.name} ({best_melee_weapon=}, {reach_weapons=})")
                continue
            if weapon.range[0] < distance:
                expected_damage /= 2
            attack_options.append((weapon, expected_damage, True))

        return attack_options

    def _get_closest_enemies(self, enemies: list[Creature]) -> tuple[list[Creature], float]:
        """Return the closest enem(ies) and their distance."""
        closest_distance = None
        closest_targets = []

        for enemy in enemies:
            distance = get_distance(self.position, enemy.position)
            if closest_distance is None or distance < closest_distance:
                closest_distance = distance
                closest_targets = [enemy]
            elif distance == closest_distance:
                closest_targets.append(enemy)

        return closest_targets, closest_distance

    def _get_expected_damages(
        self, weapons: list[Weapon], distance: Optional[float] = None
    ) -> list[tuple[Weapon, float]]:
        """Filter to usable weapons and return expected damage.

        If attack roll would incur disadvantage (e.g. ranged in melee, or at long range), divide
        expected damage in half.

        If weapon has a special trait, raise its expected damage to equal whichever weapon has the
        highest raw expected damage.
        """
        two_handed = self._get_num_free_hands() >= 2
        usable_weapons = self._usable_weapons(weapons, distance_from_target=distance)
        if not usable_weapons:
            return []

        weapon_damages = []
        for weapon in usable_weapons:
            expected_damage = weapon.roll_damage(
                two_handed=two_handed,
                damage_modifier=self._get_attack_modifier(weapon),
                use_average=True,
            ).total
            if distance is None:
                logger.debug(f"{self.name}: {weapon.name} - {expected_damage} average damage")
                pass
            elif distance <= 5:
                if not weapon.melee:
                    # Disadvantage for using ranged in melee
                    expected_damage /= 2
                logger.debug(
                    f"{self.name}: {weapon.name} - {expected_damage} average damage in melee"
                )
            else:  # Ranged (or maybe reach)
                if distance == 10 and weapon.reach:
                    logger.debug(
                        f"{self.name}: {weapon.name} - {expected_damage} average reach damage"
                    )
                    pass
                elif weapon.range[0] < distance:
                    # Disadvantage for firing at range
                    expected_damage /= 2
                    logger.debug(
                        f"{self.name}: {weapon.name} - {expected_damage} average damage at long range"
                    )
                else:
                    logger.debug(
                        f"{self.name}: {weapon.name} - {expected_damage} average damage at range"
                    )
            weapon_damages.append([weapon, expected_damage])

        # If a weapon has a special trait, assuming it's more valuable than its raw damage suggests
        # and set it as equal best
        best_damage = max(weapon[1] for weapon in weapon_damages)
        for i, option in enumerate(weapon_damages):
            if option[0].traits is not None:
                weapon_damages[i][1] = best_damage

        return [tuple(option) for option in weapon_damages]

    def _get_ideal_distance(self) -> float:
        """Compute ideal distance from nearest enemy to maximise expected damage dealt."""
        ideal_weapon = None
        ideal_distance = 5
        max_expected_damage = 0

        for weapon, expected_damage in self._get_expected_damages(self.weapons):
            if expected_damage > max_expected_damage:
                ideal_weapon = weapon
                max_expected_damage = expected_damage
                if weapon == self.best_melee_weapon or weapon.range is None:
                    ideal_distance = 10 if weapon.reach else 5
                elif weapon.range is not None:
                    ideal_distance = weapon.range[0]
            elif expected_damage == max_expected_damage:
                ideal_weapon = weapon
                # If have a weapon with equal damage but allows distance, use that
                if (weapon.range is not None) and (weapon != self.best_melee_weapon):
                    ideal_distance = max(ideal_distance, weapon.range[0])
                elif weapon.reach:
                    ideal_distance = max(ideal_distance, 10)

        logger.debug(
            f"Ideal distance is {ideal_distance} ft for {ideal_weapon}, {max_expected_damage=}"
        )

        return ideal_distance

    def _get_modifier(
        self, skill_or_ability: Union[Ability, Skill, Collection[Union[Ability]]]
    ) -> int:
        """Get the modifier for an ability or skill.

        If multiple skills or abilities are passed, return whichever modifier is highest.
        """
        if isinstance(skill_or_ability, (Ability, Skill)):
            skill_or_ability = [skill_or_ability]

        best_modifier = -5
        for option in skill_or_ability:
            if isinstance(option, Ability):
                ability = option
                skill = None
            if isinstance(option, Skill):
                skill = option
                ability = SKILL_MAPPING[option]

            modifier = (getattr(self.abilities, ability.name) - 10) // 2
            if skill is not None:
                if skill in self.skill_expertises:
                    modifier += self.proficiency * 2
                elif skill in self.skill_proficiencies:
                    modifier += self.proficiency
            if modifier > best_modifier:
                best_modifier = modifier

        return best_modifier

    def _get_num_free_hands(self, grappling: bool = False):
        """Get number of free hands available. Assume that a shield is always being held, but any
        weapon can be sheathed or unsheathed as a free object interaction.
        """
        free_hands = self.num_hands
        if self.has_shield:
            free_hands -= 1
        if grappling:
            free_hands -= 1

        return free_hands

    def _is_crit(self, rolled: int):
        """Other rules can apply, e.g. with certain feats."""
        return rolled == 20

    def _reset_death_saves(self, wake_up: bool = False):
        self.death_saves = {"successes": 0, "failures": 0}
        self.conditions.discard(Condition.dying)
        if wake_up:
            self.conditions.discard(Condition.unconscious)

    def _roll_hit_points(self) -> int:
        dice = f"{self.num_hit_die}d{self.hit_die}"
        const_mod = self.abilities.get_modifier(Ability.con)
        hp = roll(dice) + const_mod * self.num_hit_die

        return int(max(hp, 1))

    def _usable_weapons(
        self, weapons: list[Weapon], distance_from_target: Optional[float] = None
    ) -> list[Weapon]:
        """Return a bool indicating whether a weapon can be used to attack this turn.

        Must meet the following criteria:

        1. Have at least 1 round/quantity left
        2. If two-handed only, have enough hands available
        3. If `self.different_attacks == True`, not have been used already this turn
        4. If `distance_from_target` is not None, be at least in long range
        """
        two_hands_free = self._get_num_free_hands() >= 2
        usable_weapons = []
        for weapon in weapons:
            if weapon.quantity < 1:
                continue
            if weapon.two_handed_damage and not weapon.damage and not two_hands_free:
                continue
            if self.different_attacks and weapon.name in self.weapons_used_this_turn:
                continue
            if distance_from_target is not None:
                if weapon.range is not None:
                    max_range = weapon.range[1]
                elif weapon.reach:
                    max_range = 10
                else:
                    max_range = 5
                if distance_from_target > max_range:
                    continue
            usable_weapons.append(weapon)

        return usable_weapons

    def __repr__(self) -> str:
        return f"{self.name}: {self.hp}/{self.max_hp} hp {self.position}"
