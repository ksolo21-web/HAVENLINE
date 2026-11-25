# Detached input routing regression

Use the portable replay from the WIP branch with an existing workspace containing the renderer lock, a repository with the exact pinned base commit, and a fresh output folder. Use the existing shared headless lock. This loads the actual opening in an isolated profile with a test-only input overlay and routes synthesized viewport events. The ordinary input handler and simulated animation marker are separate. No real swing, OS/device timing, or changes to the playable build.
