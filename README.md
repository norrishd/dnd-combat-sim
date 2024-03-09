# dnd-combat-sim

A combat simulator for the world's greatest roleplaying game: Dungeons & Dragons 5e

## Done

- combat / creatures
  - [x] rolling init
  - [x] dealing and receiving melee damage
  - [x] critical hits
  - [x] instant death for damage exceeding max HP
  - [x] two-handed weapons
  - [x] death saving throws
  - [x] auto-failure for damage while down
  - [x] multiple attacks per turn
  - [x] ammunition
- agent logic
  - [x] choose best attack(s) using expected value, assuming a hit
- simulation
  - [x] 1v1 combat for two melee creatures whaling on each other
  - [x] run many simulations to get stats
- content
  - [x] all simple & martial weapons
  - [x] a dozen sample monsters

## TODOs

- 1D movement
- thrown weapons
- attacking
  - advantage, disadvantage
  - damage resistances and vulnerabilities
  - spells
  - AOE attacks
- agent logic
  - simple movement: moving into range
  - choose an enemy to target x smart attack to use
  - creature memory (e.g. keep attacking same enemy round to round)
  - tactical movement
- combat mechanics
  - 1D movement
  - factor in distance for ranged weapons
  - bonus actions
  - 2D movement
  - conditions
  - traits
  - non-attack actions
  - skill checks
  - saving throws
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
  - skeleton 68%\*
  - haven't implemented nimble escape
- gnoll vs hobgoblin (1/2)
- zombie (1/4)
- orc vs lizardfolk (1/2)
- half-ogre vs hippogriff (1)
- mimic vs ogre (2)
