from dnd_combat_sim.attack import Attack


class TestAttack:
    def test_attack_init(self):
        weapon = Attack.init("pseudopod")
