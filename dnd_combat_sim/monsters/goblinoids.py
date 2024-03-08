from dnd_combat_sim.utils import simple_monster
from dnd_combat_sim.weapons import (
    battleaxe_strong,
    greataxe,
    greatclub_strong,
    javelin,
    javelin_strong,
    longbow,
    longsword,
    scimitar,
)

goblin = simple_monster("Goblin", 15, "2d6", [8, 14, 10, 10, 8, 8], [scimitar])
half_ogre = simple_monster(
    "Half-Ogre", 12, "4d10", [17, 10, 14, 7, 9, 10], [battleaxe_strong, javelin_strong]
)
hobgoblin = simple_monster("Hobgoblin", 18, "2d8", [13, 12, 12, 10, 10, 9], [longsword], [longbow])
ogre = simple_monster("Ogre", 11, "7d10", [19, 8, 16, 5, 7, 7], [greatclub_strong, javelin_strong])
orc = simple_monster("Orc", 13, "2d8", [16, 12, 16, 7, 11, 10], [javelin, greataxe])
