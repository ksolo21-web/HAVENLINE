# Combat audio and recovery

Two independent disposable profiles on `34df87a8195553c4636aa374ac3bfc11054a3bbd` recorded ordinary player inputs, the health HUD, accepted Godot audio voices and actual playing WAV streams from `res://field_opening.tscn`. On both routes, the HUD showed 4, 3, 2, 1, 0 and 4 HP. The character stayed down for 63 physics ticks, or 1.05 seconds.

| Scene state | Hurt ticks | Fall | Recovery | Recovery position |
| --- | --- | --- | --- | --- |
| Before buying the hearth | 318, 471, 570, 669 | Tick 669 | Tick 732 | Initial hearth plot (0, 0, 2.4) |
| After buying the hearth | 1361, 1465, 1609, 1711 | Tick 1711 | Tick 1774 | Inside the paid camp (1.72, 0, 1.80) |

Each route registered five enemy attack voices, four hurt voices, one fall and one recovery. The audio players reported the corresponding streams on the effects bus. For each hurt, fall and recovery, the sampled player readback was within one physics tick of its accepted voice. Both routes reported zero unrecognized audio requests. The raw traces and per-cue counts distinguish accepted voice starts from requests and stream observations. [Before purchase](Combat-audio-unpaid.json) · [After purchase](Combat-audio-paid.json)
