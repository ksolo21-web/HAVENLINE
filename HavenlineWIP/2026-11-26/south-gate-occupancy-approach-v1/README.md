# Level 1 South gate occupied-close test: approach incomplete

The isolated Godot 4.7.2 X11 writer reproduced the prior 57+23 check route and reopened the South gate before attempting the new approach. Import exited 0, writer exited 7 with `incomplete safe ordinary South episode`. The captured approach used 100 regular movement steps, all grounded, with no recorded leaf contact. At t2706, the actor was at local Z 0.653635025m, 3.635mm outside the unchanged 0.650m upper entry bound. The gate was fully open and unheld. The close request was not reached; no occupied hold, release or cold reload result exists for this run. The earlier unoccupied two-cycle result is not superseded.

The approach loop checks arrival before its next movement step. One more regular step at the observed last-steps pace would predict Z about 0.6403m, within the original 0.59–0.65m window. The proposed detached retry would increase only the number of approach steps available, with the same positions, safety, gate and restore checks. This is a test-harness correction proposal, not a native retest or permission to alter the game.

Sealed source manifest: ce7efc2c0125bab084f66df14443e1b5ea839f86bdd4a348fe90f6d388a2dafe. Raw logs and local process IDs not included.
