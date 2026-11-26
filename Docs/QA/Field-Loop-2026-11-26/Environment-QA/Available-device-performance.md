# Available-device performance and touch

Commit 994ace861fbf132c5924bacc320f5608d75d9187 · Scene res://field_opening.tscn.

The Android SDK’s ADB server listed zero devices. The workspace exposed no USB input, direct-render device or display-class PCI graphics device. Physical handset performance, battery, thermals, hardware rotation and multi-touch digitizer behavior remain unmeasured.

Godot 4.7.2 ran the purchased, three-axe opening on llvmpipe (LLVM 19.1.7, 256 bits) (Mesa). Each orientation used a matching dedicated X11 display, the field’s Ultra preset, 4× MSAA and 1.0 rendering scale. The dedicated X server used a 30 Hz virtual display mode.

| Native framebuffer | Zoom | Median frame interval | 90th percentile | Frames/s over sample | Draw calls |
|---|---|---:|---:|---:|---:|
| 3840 × 2160 | 1× | 13113.7 ms | 15480.8 ms | 0.08 | 311–311 |
| 3840 × 2160 | 2× | 7531.2 ms | 10534.3 ms | 0.12 | 251–251 |
| 2160 × 3840 | 1× | 15229.7 ms | 19382.4 ms | 0.06 | 295–295 |
| 2160 × 3840 | 2× | 8180.5 ms | 9256.4 ms | 0.12 | 251–251 |

The six samples per view are wall-clock intervals between completed game draw notifications, after two warm-up frames. The benchmark removed the application frame cap and requested VSync off. The X11 driver reported that its synchronization mode could not be changed. These short intervals include simulation, rendering and scheduling. The 4K route captures had finished. A separate 720p gameplay recording still used the shared four-core CPU quota during the timing run. The timing process ran at low priority with two llvmpipe worker threads. These timings describe this constrained software-rendering run.

In a separate headless run, 360 simulation ticks at a fixed 60 Hz step took 1.478 wall-clock seconds. The median 30-tick group averaged 1.19 ms per tick, with group means from 0.53 to 16.69 ms. This measures the simulation and engine loop with rendering disabled.

**Landscape** passed 11/11 camera, settings and input assertions.
**Portrait** passed 11/11 camera, settings and input assertions.

The viewport received indexed Godot touch events through its input dispatcher. The checks cover proportional 1.5× zoom, both 1× and 2× limits, a canceled touch, movement ownership and a fixed camera angle. The framebuffer dimensions were independently read from the captured GPU image and matched the full display in each orientation. Godot’s canvas-scaled ViewportTexture size accessor reported a different size, which is retained separately in the raw results. Each orientation started independently.

[Raw samples and assertions](Available-device-timings.json)

## On-device measurement

1. On an arm64 test handset in a dedicated test user, install `Havenline-Field-Android-arm64-debug.apk` from the shared review downloads with ADB. Alfred can also open the [source project at the tested revision](https://github.com/ksolo21-web/HAVENLINE/tree/994ace861fbf132c5924bacc320f5608d75d9187/HavenlineLevel1) in Godot 4.7.2. Verify its SHA-256 against the [package manifest](../Package-SHA256SUMS.txt). Launch com.havenline.fieldreview, earn the furnace and the three-tool upgrade, then use the same position at the side of the court for each take.
2. Record the handset model, OS, graphics driver, temperature and quality setting. For each orientation and requested refresh mode, inspect the display’s active mode with adb shell dumpsys display and the game layer’s buffer dimensions with adb shell dumpsys SurfaceFlinger. Capture the compositor’s actual mode while the game is in the foreground. A nominal panel resolution or advertised refresh rate does not verify the app surface.
3. Warm the scene for two minutes and use a two-finger spread to select the normal and 2× views. Capture at least 60 seconds per condition using Android Studio System Trace or Perfetto with FrameTimeline enabled. Select the game’s actual SurfaceView frame presentations. Report actual frame intervals, median, 90th/99th percentiles, and missed display deadlines, with orientation and refresh rate for each run.
4. A 60 Hz presentation budget is 16.67 ms and 120 Hz is 8.33 ms. The project’s simulation runs at 60 Hz. A 120 Hz output surface alone cannot establish 120 distinct simulation updates per second. Distinguish app frames from compositor repeats, and record any thermal or refresh-mode changes during each take. This checklist is unrun on hardware.
