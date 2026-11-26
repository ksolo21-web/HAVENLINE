# Replay the camp production review

The recording starts from a copy of the player-earned owl encounter checkpoint from the previous Level 1 trial. The opening inventory contains nine wood, two stones and two portions of raw meat. Each run creates a separate marked disposable profile. The driver uses the gameplay scene, its touch joystick, gate control and ordinary camera.

The gameplay film uses Godot's fixed clock at 16 frames per second, its native 1280 × 720 viewport, 60 Hz physics and its stereo master mix. Chapter cuts omit stretches of walking or waiting. The full physical route also runs between chapters. The individual 3840 × 2160 JPEGs come from separate Godot runs at the default camera zoom and a real touch pinch. Phone frame rate requires a device measurement.

Run the commands from this Replay directory after setting `HL_GAME_PROJECT` to the prepared trial project. Python, FFmpeg and Godot 4.7.2 are required. The mux checks every decoded frame and compares the stereo AAC output with the engine samples. It also uses NumPy and SciPy.

## Check the actual gameplay route

```bash
trial_run=$(mktemp -d)
bash run.sh "$trial_run" "$PWD/production-route.json" headless 16
python verify.py "$trial_run" "$trial_run/receipts.json"
```

## Capture video and sound

Set `HL_DISPLAY` and `HL_XAUTHORITY` to the review display. The run records native video and audio using a local encoder.

```bash
film_run=$(mktemp -d)
bash run.sh "$film_run" "$PWD/production-route.json" record 16
python verify.py "$film_run" "$film_run/receipts.json"
python mux.py "$film_run" "$film_run/Camp-production.mp4" 16
```

## Capture native 4K stills

Use a 3840 × 2160 review display. The second route pinches the gameplay camera at the sawmill and drill.

```bash
stills_run=$(mktemp -d)
zoom_run=$(mktemp -d)
bash run.sh "$stills_run" "$PWD/production-route.json" plates 24
bash run.sh "$zoom_run" "$PWD/saw-closeups.json" plates 24
```
