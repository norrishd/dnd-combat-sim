import argparse

from dnd_combat_sim.creature import Creature
from dnd_combat_sim.encounter import MultiEncounter1v1
from dnd_combat_sim.utils import MONSTERS

if __name__ == "__main__":
    choices = MONSTERS.index.tolist()
    parser = argparse.ArgumentParser(description="Run a combat simulation.")
    parser.add_argument("creature1", nargs="?", default="orc", choices=choices)
    parser.add_argument("creature2", nargs="?", default="bullywug", choices=choices)
    parser.add_argument("-n", "--num_runs", type=int, default=1)
    args = parser.parse_args()

    creature1 = Creature.init(args.creature1)
    creature2 = Creature.init(args.creature2)

    encounter = MultiEncounter1v1(creature1, creature2, num_runs=args.num_runs)
    encounter.run(to_the_death=True)
