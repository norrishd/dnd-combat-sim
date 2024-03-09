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
- agent logic
  - [x] choose best attack(s) using expected value, assuming a hit
- simulation
  - [x] 1v1 combat for two melee creatures whaling on each other
  - [x] run many simulations to get stats
- content
  - [x] all simple & martial weapons
  - [x] a dozen sample monsters

## TODOs

- attacking
  - [ ] ranged weapons
  - [ ] thrown weapons
- agent logic

  - [ ] choose an attack, considering expected damage and chance of hitting
  - [ ] choose an enemy to target \* smart attack to use
  - [ ] creature memory (e.g. keep attacking same enemy round to round)

- [ ] factor in distance for ranged weapons
- [ ] advantage, disadvantage
- [ ] damage resistances and vulnerabilities
- [ ] bonus actions
- [ ] 1D movement
  - [ ] 2D movement
- [ ] status effects
- [ ] non-attack actions
- [ ] position and movement
- [ ] visualisation
- [ ] picking up items
- [ ] spells?
