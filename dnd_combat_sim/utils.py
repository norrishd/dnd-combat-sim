from typing import Optional

from dnd_combat_sim.attack import MeleeAttack, RangedAttack
from dnd_combat_sim.creature import Creature, Stats


def parse_stats(
    ac: int,
    hp: str,  # e.g. 2d8
    ability_scores: list[int],  # Should be len-6 for str, dex, const, int, wis, cha):
    speed: int = 30,
):
    level, hit_die = hp.split("d")
    return Stats(
        ac=ac,
        level=int(level),
        hit_die=int(hit_die),
        speed=speed,
        strength=ability_scores[0],
        dexterity=ability_scores[1],
        constitution=ability_scores[2],
        intelligence=ability_scores[3],
        wisdom=ability_scores[4],
        charisma=ability_scores[5],
    )


def simple_monster(
    name: str,
    ac: int,
    hp: str,
    stats: list[int],  # Should be len-6 for str, dex, const, int, wis, cha
    melee_attacks: Optional[list[MeleeAttack]] = None,
    ranged_attacks: Optional[list[RangedAttack]] = None,
    speed: int = 30,
    make_death_saves: bool = False,
):
    """Create a simple monster with basic stats and attacks."""
    return Creature(
        name=name,
        stats=parse_stats(ac, hp, stats, speed),
        melee_attacks=melee_attacks,
        ranged_attacks=ranged_attacks,
        make_death_saves=make_death_saves,
    )
