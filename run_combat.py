import argparse

from dnd_combat_sim.encounter import MultiEncounter1v1
from dnd_combat_sim.monsters import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a combat simulation.")
    parser.add_argument("-n", "--num_runs", type=int, default=1)
    args = parser.parse_args()

    encounter = MultiEncounter1v1(giant_rat, goblin, num_runs=args.num_runs)
    encounter.run(to_the_death=True)
