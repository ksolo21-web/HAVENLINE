# Rebuild the reviewed Godot field

Run the following from this directory with an existing Havenline clone. Use a new output directory.

```sh
python prepare.py /path/to/HAVENLINE /tmp/havenline-fold-playtest
godot --headless --editor --path /tmp/havenline-fold-playtest --import
```

The script reads the source revision named in Reviewed-files.json, checks every listed file digest, reconstructs the furnace model from its committed parts when necessary, and extracts the three original fitted axe textures from the checked-in GLB. The default scene is `res://field_opening.tscn`. Use Godot 4.7.2 for the recorded result. The Android package uses the **Android World Review** preset and the existing trial signer.
