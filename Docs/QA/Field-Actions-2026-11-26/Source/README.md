# Reproduce the Level 1 field

The manifest records the gameplay commit, main scene and each source file’s SHA-256. Use a Git checkout that includes the trial branch. From this directory, run the following commands with a new output directory.

```sh
python prepare.py /path/to/HAVENLINE /tmp/havenline-field-actions-review
godot --headless --editor --path /tmp/havenline-field-actions-review --import
```

The project uses Godot 4.7.2. Start the normal entry scene `res://field_opening.tscn` with a disposable profile to reproduce play. The release package uses the arm64 Android debug export preset and the existing trial signing identity. The manifest covers source data, including the imported rigs, audio and QA code. [Source hashes](Reviewed-files.json)
