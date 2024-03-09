from dnd_combat_sim.attack import MeleeAttack, RangedAttack

### Melee weapons ###
# Simple
club = MeleeAttack("Club", damage="1d4 bludgeoning", light=True)
dagger = MeleeAttack("Dagger", damage="1d4 piercing", range=(20, 60), finesse=True, light=True)
greatclub = MeleeAttack("Greatclub", two_handed_damage="1d8 bludgeoning")
handaxe = MeleeAttack("Handaxe", damage="1d6 slashing", range=(20, 60), light=True)
javelin = MeleeAttack("Javelin", damage="1d6 piercing", range=(30, 120))
light_hammer = MeleeAttack("Light hammer", damage="1d4 bludgeoning", range=(30, 120), light=True)
mace = MeleeAttack("Mace", damage="1d6 bludgeoning")
quarterstaff = MeleeAttack(
    "Quarterstaff", damage="1d6 bludgeoning", two_handed_damage="1d8 bludgeoning"
)
sickle = MeleeAttack("Sickle", damage="1d4 slashing", light=True)
spear = MeleeAttack(
    "Spear", damage="1d6 piercing", two_handed_damage="1d8 piercing", range=(20, 60)
)

# Martial
battleaxe = MeleeAttack("Battleaxe", damage="1d8 slashing", two_handed_damage="1d10 slashing")
flail = MeleeAttack("Flail", damage="1d8 bludgeoning")
glaive = MeleeAttack("Glaive", two_handed_damage="1d10 slashing", reach=10, heavy=True)
greataxe = MeleeAttack("Greataxe", two_handed_damage="1d12 slashing", heavy=True)
halberd = MeleeAttack("Halberd", two_handed_damage="1d10 slashing", reach=10, heavy=True)
lance = MeleeAttack("Lance", two_handed_damage="1d12 piercing", reach=10, heavy=True)
longsword = MeleeAttack("Longsword", damage="1d8 slashing", two_handed_damage="1d10 slashing")
maul = MeleeAttack("Maul", two_handed_damage="2d6 bludgeoning", heavy=True)
morningstar = MeleeAttack("Morningstar", damage="1d8 piercing")
pike = MeleeAttack("Pike", two_handed_damage="1d10 piercing", reach=10, heavy=True)
rapier = MeleeAttack("Rapier", damage="1d8 piercing", finesse=True)
scimitar = MeleeAttack("Scimitar", damage="1d6 slashing", finesse=True, light=True)
shortsword = MeleeAttack("Shortsword", damage="1d6 piercing", finesse=True, light=True)
trident = MeleeAttack(
    "Trident", damage="1d6 piercing", two_handed_damage="1d8 piercing", range=(20, 60)
)
unarmed_strike = MeleeAttack("Unarmed Strike", damage="1d1 bludgeoning")
war_pick = MeleeAttack("War Pick", damage="1d8 piercing")
warhammer = MeleeAttack("Warhammer", damage="1d8 bludgeoning", two_handed_damage="1d10 bludgeoning")
whip = MeleeAttack("Whip", damage="1d4 slashing", reach=10, finesse=True)


### Ranged attacks ###
# Simple
light_crossbow = RangedAttack(
    "Light Crossbow", damage="1d8 piercing", range=(80, 320), loading=True
)
dart = RangedAttack("Dart", damage="1d4 piercing", range=(20, 60), thrown=True)
shortbow = RangedAttack("Shortbow", damage="1d6 piercing", range=(80, 320))
sling = RangedAttack("Sling", damage="1d4 bludgeoning", range=(30, 120))

# Martial
blowgun = RangedAttack("Blowgun", damage="1d1 piercing", range=(25, 100), loading=True)
hand_crossbow = RangedAttack("Hand Crossbow", damage="1d6 piercing", range=(30, 120), loading=True)
heavy_crossbow = RangedAttack(
    "Heavy Crossbow", damage="1d10 piercing", range=(100, 400), heavy=True, loading=True
)
longbow = RangedAttack("Longbow", damage="1d8 piercing", range=(150, 600), heavy=True)
net = RangedAttack("Net", range=(5, 15), thrown=True)


### Monster attacks ###
# Weapons
battleaxe_strong = MeleeAttack(
    "Battleaxe", damage="2d8 slashing", two_handed_damage="2d10 slashing"
)
greatclub_strong = MeleeAttack("Greatclub", two_handed_damage="2d8 bludgeoning")
heavy_club = MeleeAttack("Heavy Club", damage="1d6 bludgeoning")
javelin_strong = MeleeAttack("Javelin", damage="2d6 piercing", range=(30, 120))

# Natural attacks
beak_large = MeleeAttack("Beak", damage="1d10 piercing")
bite_small = MeleeAttack("Bite", damage="1d4 piercing")
bite = MeleeAttack("Bite", damage="1d6 piercing")
bite_big = MeleeAttack("Bite", damage="1d8 piercing")
claws = MeleeAttack("Claws", damage="2d6 piercing")
