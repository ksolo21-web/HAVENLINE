# Reading the Level 1 test results

The [Android package](Android.json) identifies the signed game. The [independent critic](../References/Independent-review.md) compares actual gameplay with the GitHub footage and art.

The complete [native suite](Reviewed-native/Native-results.json) and [progression replay](Reviewed-progression/Completion-results.json) use the same runtime as the signed game. The [QA revision](../Source/Reviewed-QA-files.json) adds four changes to the test harness. They make the legacy tower check recognize a visible bolt that is itself the mesh, give an unused furnace effect an owner in a counter-only test scene, steer through the public work area to buy the saw, and check whether the whole character has cleared a gate. The signed APK excludes these tests. To reconstruct the QA checkout, run `python Source/prepare.py REPO_PATH NEW_PROJECT_PATH --qa` from the release evidence directory. Omit `--qa` to reconstruct the signed game sources. [Before those test corrections](Native/Native-results.json)

A second, unmodified 16-launch drive on the exact game commit also achieved all 219 progression checks. It preserves three original failure observations from the investigation and fresh evidence from the same saved worker claim. [Progression and claim replay](Claim-recheck/README.md)

The [packed gameplay replay](Signed-production-floor.json), [packed quarry replay](../Stone/Signed-apk-resource-mining.json) and [packed save upgrades](Signed-layout-migration.json) used Godot resources read from the signed APK in the desktop player. The [Git reconstruction](Reconstruct-game.json) verified all 650 listed source files in a fresh directory. The [download record](Private-download.json) covers the authenticated mobile download and its range response.
