import argparse
import json

from dnd_combat_sim.creature import Creature
from dnd_combat_sim.encounter import MultiEncounter1v1
from dnd_combat_sim.utils import MONSTERS, cr_to_float

if __name__ == "__main__":
    choices = MONSTERS.index.tolist()
    parser = argparse.ArgumentParser(description="Run a combat simulation.")
    parser.add_argument("creature1", nargs="?", default="orc", choices=choices)
    parser.add_argument("creature2", nargs="?", default="bullywug", choices=choices)
    parser.add_argument("-d", "--death_saves", action="store_true")
    parser.add_argument("-n", "--num_runs", type=int, default=1)
    parser.add_argument("-m", "--monsters", action="store_true", help="List available monsters")
    args = parser.parse_args()

    if args.monsters:
        MONSTERS["cr_float"] = MONSTERS["cr"].apply(cr_to_float)

        print(MONSTERS.reset_index().sort_values(["cr_float", "name"]).set_index("name")["cr"])
        exit()

    creature1 = Creature.init(args.creature1, make_death_saves=args.death_saves, start_x=0)
    creature2 = Creature.init(args.creature2, make_death_saves=args.death_saves, start_x=100)

    encounter = MultiEncounter1v1(creature1, creature2, num_runs=args.num_runs)
    encounter.run()
