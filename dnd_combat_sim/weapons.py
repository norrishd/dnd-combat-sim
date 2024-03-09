# from dnd_combat_sim.attack import MeleeAttack, RangedAttack

# ### Melee weapons ###
# # Simple
# club = MeleeAttack("club", damage="1d4 bludgeoning", light=True)
# dagger = MeleeAttack("dagger", damage="1d4 piercing", range=(20, 60), finesse=True, light=True)
# greatclub = MeleeAttack("greatclub", two_handed_damage="1d8 bludgeoning")
# handaxe = MeleeAttack("handaxe", damage="1d6 slashing", range=(20, 60), light=True)
# javelin = MeleeAttack("javelin", damage="1d6 piercing", range=(30, 120))
# light_hammer = MeleeAttack("light hammer", damage="1d4 bludgeoning", range=(30, 120), light=True)
# mace = MeleeAttack("mace", damage="1d6 bludgeoning")
# quarterstaff = MeleeAttack(
#     "quarterstaff", damage="1d6 bludgeoning", two_handed_damage="1d8 bludgeoning"
# )
# sickle = MeleeAttack("sickle", damage="1d4 slashing", light=True)
# spear = MeleeAttack(
#     "spear", damage="1d6 piercing", two_handed_damage="1d8 piercing", range=(20, 60)
# )

# # Martial
# battleaxe = MeleeAttack("battleaxe", damage="1d8 slashing", two_handed_damage="1d10 slashing")
# flail = MeleeAttack("flail", damage="1d8 bludgeoning")
# glaive = MeleeAttack("glaive", two_handed_damage="1d10 slashing", reach=10, heavy=True)
# greataxe = MeleeAttack("greataxe", two_handed_damage="1d12 slashing", heavy=True)
# halberd = MeleeAttack("halberd", two_handed_damage="1d10 slashing", reach=10, heavy=True)
# lance = MeleeAttack("lance", two_handed_damage="1d12 piercing", reach=10, heavy=True)
# longsword = MeleeAttack("longsword", damage="1d8 slashing", two_handed_damage="1d10 slashing")
# maul = MeleeAttack("maul", two_handed_damage="2d6 bludgeoning", heavy=True)
# morningstar = MeleeAttack("morningstar", damage="1d8 piercing")
# pike = MeleeAttack("pike", two_handed_damage="1d10 piercing", reach=10, heavy=True)
# rapier = MeleeAttack("rapier", damage="1d8 piercing", finesse=True)
# scimitar = MeleeAttack("scimitar", damage="1d6 slashing", finesse=True, light=True)
# shortsword = MeleeAttack("shortsword", damage="1d6 piercing", finesse=True, light=True)
# trident = MeleeAttack(
#     "trident", damage="1d6 piercing", two_handed_damage="1d8 piercing", range=(20, 60)
# )
# unarmed_strike = MeleeAttack("unarmed strike", damage="1d1 bludgeoning")
# war_pick = MeleeAttack("war pick", damage="1d8 piercing")
# warhammer = MeleeAttack("warhammer", damage="1d8 bludgeoning", two_handed_damage="1d10 bludgeoning")
# whip = MeleeAttack("whip", damage="1d4 slashing", reach=10, finesse=True)


# ### Ranged attacks ###
# # Simple
# light_crossbow = RangedAttack(
#     "light crossbow", damage="1d8 piercing", range=(80, 320), loading=True
# )
# dart = RangedAttack("dart", damage="1d4 piercing", range=(20, 60), thrown=True)
# shortbow = RangedAttack("shortbow", damage="1d6 piercing", range=(80, 320))
# sling = RangedAttack("sling", damage="1d4 bludgeoning", range=(30, 120))

# # Martial
# blowgun = RangedAttack("blowgun", damage="1d1 piercing", range=(25, 100), loading=True)
# hand_crossbow = RangedAttack("hand crossbow", damage="1d6 piercing", range=(30, 120), loading=True)
# heavy_crossbow = RangedAttack(
#     "heavy crossbow", damage="1d10 piercing", range=(100, 400), heavy=True, loading=True
# )
# longbow = RangedAttack("longbow", damage="1d8 piercing", range=(150, 600), heavy=True)
# net = RangedAttack("net", range=(5, 15), thrown=True)


# ### Monster attacks ###
# # Weapons
# battleaxe_strong = MeleeAttack(
#     "battleaxe", damage="2d8 slashing", two_handed_damage="2d10 slashing"
# )
# greatclub_large = MeleeAttack("greatclub", two_handed_damage="2d8 bludgeoning")
# heavy_club = MeleeAttack("heavy club", damage="1d6 bludgeoning")  # Lizardfolk
# javelin_large = MeleeAttack("javelin", damage="2d6 piercing", range=(30, 120))

# # Natural attacks
# beak_large = MeleeAttack("beak", damage="1d10 piercing")
# bite_small = MeleeAttack("bite", damage="1d4 piercing", finesse=True)
# bite_small_b = MeleeAttack("bite", damage="1d4 bludgeoning", finesse=True)
# bite = MeleeAttack("bite", damage="1d6 piercing")
# bite_big = MeleeAttack("bite", damage="1d8 piercing")
# bite_big_acid = MeleeAttack("bite", damage="1d8 piercing", bonus_damage="1d8 acid")
# claws_large = MeleeAttack("claws", damage="2d6 piercing")
# pseudopod = MeleeAttack("pseudopod", damage="1d8 bludgeoning")  # TODO apply adhesive (grappled)
# slam = MeleeAttack("slam", damage="1d6 bludgeoning")
