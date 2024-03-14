# dnd-combat-sim

A combat simulator for the world's greatest roleplaying game: Dungeons & Dragons 5e.

Ever wanted to see who would win in a 5 skeletons vs 1 ogre fight? Now you can!

## Setup

    cd dnd-combat-sim
    pip install poetry
    poetry install 

## Usage

    poetry shell  # Activate virtual environment
    python run_combat.py {MONSTER1] [MONSTER2] [-n NUM_ENCOUNTERS]

E.g. to see a skeleton go at it with a zombie:

    python run_combat.py skeleton zombie

To run 100 simulations of an orge fighting a mimic and tally victories:

    python run_combat.py ogre mimic -n 100

To list available monsters:

    python run_combat --monsters

## Implemented

### Agent logic
  - [x] choosing best attack(s) weighted by expected damage value, assuming a hit

#### Combat / creatures
- [x] dealing and receiving melee damage
- [x] instant death for damage exceeding max HP
- [x] death saving throws
- [x] auto-failure for damage while down
- [x] critical hits
- [x] multiple attacks per turn
- [x] damage resistance, vulnerability and immunity
- [x] traits (e.g. undead fortitude)
- [x] weapon/attack traits (e.g. mimic pseudopod)
- [x] temporary effects:
  - Grappled
- [x] advantage/disadvantage from temporary effects

### Content
- [x] 20 sample monsters
- [x] all simple & martial weapons
- [x] natural attacks from all implemented monsters

### Simulation
- [x] rolling initiative
- [x] 1v1 combat for two melee creatures whaling on each other
- [x] run many simulations to get stats

### Traits
- Creature traits
  - [x] Grappler
  - [x] Martial advantage
  - [x] Pack tactics
  - [x] Undead fortitude
- Weapon traits
  - [x] Adhesive

### Weapons
- [x] two-handed damage & logic to use one or two handed
- [x] ammunition
- [x] special weapon traits, e.g. lance, net, pseudopod
- [ ] throwing weapons


## TODOs

- basic 1D movement
- Rampage: temporary new bonus action option
- thrown weapons
- attacking
  - saving throw attacks
  - spells
  - AOE attacks
- agent logic
  - simple movement: moving into range
  - choose an enemy to target x smart attack to use
  - creature memory (e.g. keep attacking same enemy round to round)
  - tactical movement
- combat mechanics
  - factor in distance for ranged weapons
  - bonus actions
  - 2D movement
  - non-attack actions
  - skill checks
- visualisation

## Showdown

- commoner vs giant rat (0-1/8):
  - giant rat 89%
- bandit vs kobold (1/8)
  - bandit 78%
- cultist vs guard (1/8)
  - guard 73%
- bullywug vs flying sword (1/4)
  - flying sword 69%
- goblin vs skeleton (1/4)
  - skeleton 68%
  - haven't implemented nimble escape or ranged dynamics
- gnoll vs hobgoblin (1/2)
  - gnoll 70%
    - Haven't implemented rampage (though not relevant for 1v1)
- zombie vs blink dog (1/4)
  - zombie 85%
    - skeleton is vulnerable to bludgeoning damage
- orc vs lizardfolk (1/2)
  - lizardfolk 78%
- half-ogre vs hippogriff (1)
  - half-ogre 69%
- mimic vs ogre (2)

## Combat flow:

- roll initiative
- start round. Per creature, in initiative order
  - start turn: check if dying, incapacitated, etc
  - resolve effecs, e.g. death saving throw, end special conditions, take poison damage
  - choose action or bonus action, factoring in remaining movement
  - potentially move to achieve action/bonus action
  - potentially trigger one or more opportunity attack(s)
  - check if incapacitated, unconscious etc
  - start action on target
  - potentially handle a reaction, e.g. counter-spell, shield or undead fortitude
  - re-assess action on target (e.g. maybe attack now misses)
  - resolve action, e.g. do damage
  - potentially handle reaction, e.g. hellish rebuke, undead fortitude or mud mephit exploding
  - check if incapacitated, unconscious etc
  - choose remaining action or bonus action, factoring in remaining movement
  - potentially move to achieve action/bonus action
  - potentially trigger one or more opportunity attack(s)
  - check if incapacitated, unconscious etc
  - start action on target
  - potentially handle a reaction, e.g. counter-spell, shield or undead fortitude
  - re-assess action on target (e.g. maybe attack now misses)
  - resolve action, e.g. do damage
  - potentially handle reaction, e.g. hellish rebuke, undead fortitude or mud mephit exploding
  - check if incapacitated, unconscious etc
