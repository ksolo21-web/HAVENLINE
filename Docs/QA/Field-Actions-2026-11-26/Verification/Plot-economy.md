# Level 1 plot economy

The B opening marker shows 200 timber at 05.40 s. A single visit fills it by 06.10 s and the furnace becomes visible at 06.30 s. The B axe tile reads $100 at 13.00 s. The neighboring tile reads $175 at 13.60 s. The A fishing upgrade reads 160 cash at 12.00 s. Both cash payments show separate objects leaving the character’s pack.

## Playable prices

Each visible bundle represents 10 raw units. A tree or mining source yields three physical bundles. A normal wolf yields two meat pieces and a boss yields five. The hearth costs seven trees’ worth from an empty pack, with ten timber left if every drop is collected. The material recipes after the hearth are Havenline tuning. The source clips do not establish a wood-to-cash exchange rate or the value of an individual rendered drop.

| Purchase | Raw unit price | Physical receipts | Paid at |
|---|---|---:|---:|
| center hearth | 200 wood | 20 | 36.00 s |
| survivor plot | 80 wood | 8 | 102.25 s |
| expansion 1 | 120 wood, 60 stone | 18 | 189.62 s |
| storage wood | 100 wood | 10 | 195.73 s |
| storage stone | 80 wood, 60 stone | 14 | 200.13 s |
| storage meat | 70 wood, 50 meat | 12 | 205.68 s |
| expansion 2 | 150 wood, 100 stone | 25 | 216.63 s |
| watchtower | 120 wood, 100 stone | 22 | 221.90 s |
| orbit upgrade | 60 stone, 40 meat | 10 | 225.85 s |

## Native gameplay evidence

The uninterrupted run started with 0 carried units, 0 receipts and 200 on the hearth tile. It used the ordinary touch controls in a disposable profile. The first trip brought 90 timber back on nine receipts and left 110 on the floor. The second brought 110 timber back on eleven receipts and triggered construction at 36.00 s. The run used an initial two-trip opening and later gathered a large reserve before returning to camp. It recorded nine purchase cues, 196 individual pickup receipts, all eight camp purchases and the survivor purchase. The final axe was paid by 225.85 s. This is one fixed-step gameplay run, with time measured on the game clock.

The verified save path retains the old price of any plot with a committed v1–v5 payment, including partially sponsored survivors. It applies new prices to every untouched plot. Previously owned purchases and all material receipts retain their values. Tests passed for partial and already-complete contracts, wrong duplicated contracts, stock conservation, fresh save, restart and failed-write recovery. The independent end-to-end run passed 208 checks in 16 fresh processes, starting with a genuine version-3 save written by the prior build.

## Reference and evidence files

The three sampled source sequences, original screen-recording hashes, timestamped readouts, route observations and log hashes are listed in `Plot-economy-evidence.json`. `Plot-price-reference.jpg` shows the actual source pixels and timestamp labels.
