# Rebuild the expanded camp

The manifest identifies the tested gameplay commit, its ordinary Godot scene and each reviewed project input. From a checkout containing that commit, run the supplied extraction helper with a new output directory.

```sh
python3 prepare.py /path/to/HAVENLINE /tmp/havenline-camp-project
godot --headless --editor --path /tmp/havenline-camp-project --import
```

Godot 4.7.2 with its matching export templates can build either platform. Android also requires a configured SDK, JDK and debug keystore.

```sh
mkdir -p /tmp/havenline-camp-build
godot --headless --path /tmp/havenline-camp-project --export-release 'Linux World Review' /tmp/havenline-camp-build/Havenline-Level-1.x86_64
godot --headless --path /tmp/havenline-camp-project --export-debug 'Android World Review' /tmp/havenline-camp-build/Havenline-Camp-Production.apk
```

The ordinary launcher starts the trial in a dedicated save directory. The expanded-camp launcher opens a private copy of the previously earned camp for reviewing the machines. [Playtest instructions](../Play/README.md)
