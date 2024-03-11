from dnd_combat_sim.weapon import Weapon


class TestWeapon:
    def test_weapon_init(self):
        weapon = Weapon.init("pseudopod")
