# World One resources, encounters and tower

The linked field diagnostics document the preceding implementation of wolves, defense and streaming. Current timing and health checks are in the [five-second tree review](Trees/README.md) and [current native test results](../World/Native-suite-results.json). A second run instantiated and defeated 572 actual wolves over 200 waves at the expanded camp and the four map corners. It produced 31 alphas, peaked at four concurrent wolves, returned one meat drop group per death, and finished with no remaining enemy nodes or enemy-track registrations. A separate 500-wave seeded placement test returned 97 alphas. These counts come from different seeds and different tests. [Native results and source hashes](Native-lifecycle-results.json)

| Feature | Tuning and verified behavior |
|---|---|
| Trees and mineral sources | Playing-time regrowth takes five seconds for wood and 32 seconds for stone. Each completed three-strike source yields three loose units. Partial strikes survive streaming and saving. Leaving a falling tree resolves its already-earned fall once. A regrown source produces fresh pickup IDs. |
| Enemy waves | A successful encounter draws two to four wolves, clipped to available space, then rolls an 18% chance for one alpha. A full pack consumes no roll. The refill interval is 24 played seconds. Positions must be at least 5.2 m from the player and respect the active camp boundary and world edge. Expanding the perimeter immediately retires enemies caught by the new boundary before the next gameplay tick. Distant packs retire beyond 32 m. Defeated wolves finish a 0.72 s fall before cleanup. |
| Alphas | The same animated wolf is 1.58× the standard size, with an amber status bar, 8 HP, a 0.62-second windup, 2 bite damage and five meat. Regular wolves have 3 HP, a 0.38-second windup, 1 bite damage and two meat. An actual advancing alpha registered four rigged paws and left six native snow prints during the test. |
| Eastern watchtower | The paid tower tracks live eastern targets within 13 m. Each visible bolt travels at 13 m/s and deals one damage on arrival, with a 1.65 s reload. The unpaid tower dealt zero damage. The paid one killed an eight-health alpha. All four dedicated boss/tower audio cues started on their matching game events. |
| Loose drops | A unit can be collected once. Loose units expire after 100 played seconds. At most 72 persist in the world. Older loose items make room when this cap is reached. |
| Save and resume | Health, standing position and facing, resource cooldowns, partial strikes, loose pickups, live wolf health and homes, encounter time and random state survive a clean close. Timers advance during active play. Transient enemy attack phases and bolts restart on reload. Zero health resumes the fall and return to the protected inner court or unpaid hearth plot. Full HP and two seconds of protection accompany recovery. A three-process test at each stage closed during the fall, completed recovery on reopening, then reopened again to verify that full health and the destination were saved. [Defeat and reopening](../World/Defeat-and-reopen.json) |

The two-process save test moved the player west using ordinary touch input, then set a diagnostic injury and an 8.25-second timer. After a clean close, a new Godot process reopened at exactly `(−36.3581, 6.1931)` with 3 HP and all 8.25 seconds remaining. A separate ordinary-input grove test landed all three contacts, collected the wood and returned the distant tree to its instanced representation.

Run these commands in the World One Godot project directory. They create their own fresh, marked, disposable profiles.

```bash
godot --headless --path . --fixed-fps 60 --script res://qa_world_lifecycle.gd
godot --headless --path . --fixed-fps 60 --script res://qa_encounter_waves.gd
godot --headless --path . --fixed-fps 60 --script res://qa_world_session_resume.gd
```

Some accelerated headless shutdowns print Godot audio playback cleanup diagnostics. A verbose short-scene exit identified retained WAV and playback objects. The native wave test separately checks live enemy, target and paw registrations after cleanup.

[Watch the eastern tower fire and hit an alpha](Tower-bolt-and-impact.mp4) in the native field camera. This silent 1.9-second diagnostic stages a paid tower and a registered alpha to isolate the shot. The alpha drops from eight to seven health on impact. [Frame positions and health](Tower-flight.json)

Future survivor or worker scenes can opt into footprints by adding their living root to the `snow_track_survivors` group before spawning. A separate native test verified automatic discovery, moving footsteps, stationary behavior and exclusion of moving scenery. The same test recorded six hero prints from both soles and verified four distinct paw landings each for a wolf and an alpha. [Tracker test results](Survivor-track-discovery.json)
