# Sharp Eye

Home security system that monitors IP cameras for motion, runs YOLO object detection on motion clips, and triggers alarm/notification actions when persons or animals are detected.

## Architecture

Three independent long-running processes, launched via cron inside a single Docker container:

- **admin.py** — Flask web UI (port 8080) for camera gallery, arm/disarm control, and HSS (Home Security System) status. Supervises camera processes: starts/stops them based on UI toggle via `quicklock` file locks.
- **sharp_eye.py** (one per camera) — RTSP capture + motion detection + video recording. Spawned by the admin supervisor. Each instance runs ffmpeg for RTSP frame capture, MOG2 background subtraction for motion detection, and ffmpeg for encoding motion clips.
- **object_detector.py** — Scans `/snapshots/<camera>/` for new .mp4 files, runs YOLOv8 (OpenVINO) on each frame, sends notifications and triggers alarm actions.
- **hss_genie.py** — Monitors Paradox alarm panel via MQTT (`paradox/states/`), sends notifications on zone/partition state changes. Independent from cameras.

## Key design decisions

**File-based inter-process communication.** Camera processes write BMP frames to `/tmp` and motion videos to `/snapshots/<camera>/`. The object detector picks up .mp4 files from there. A `.json` sidecar per video contains per-frame motion metadata (bounding box coordinates in 1920x1080 space). Trigger file `/tmp/object_detection.tmp` signals the object detector to scan immediately rather than waiting for the 300s polling interval. This separation is deliberate — camera processes must run independently and do their simple capture/detect/record job. The object detector is a detached loop that works only on collected videos. This scales better than running YOLO in-process per camera.

**Process lifecycle via cron + file locks.** `quicklock` manages singleton processes — each process locks its identifier at startup. The admin supervisor checks lock state to determine if a camera is running and can `force_unlock` (kill) to stop it. Cron re-launches processes every minute; `lock()` exits immediately if already running. This pattern originated on Raspberry Pi 2B+ (no Docker, ~10 years ago) where process reliability was poor — cron provided automatic restart without manual intervention. It carried over to the current Docker/Intel setup and works well enough.

**Person detection triggers the alarm.** When the object detector sees a person with >0.75 confidence, `PerimeterPartitionProcessor` calls the admin web API (`/hss/control/motion`) which arms the Paradox alarm perimeter partition. This is a real alarm action, not just a notification. Person notification suppression is 180 seconds because a single person walking through the yard crosses multiple camera zones and would otherwise spam notifications — one alert per entry is enough.

**Animal detection is notification-only.** Animals (cats, dogs) never trigger the alarm. Suppression is 0 (every detection notifies) because the goal is tracking a cat that poops around the backyard — every sighting on every camera matters.

**Motion video 5x playback speed is intentional.** Videos are encoded at 10fps from 2fps source frames (`duration 0.1` per frame in ffconcat). This is NOT frame duplication — each source frame appears exactly once. The 5x speedup reduces the time needed to review footage. Do not "fix" this to match the source frame rate.

**YOLOv8m chosen over yolov8n for accuracy.** Both models exist in the repo. The `m` (medium) model is used deliberately because detection accuracy matters more than CPU savings for a security system. `yolov8n` is available as a fallback if CPU becomes a constraint.

**Notification system.** A custom notification service receives events via REST API. Topics: `camera_motion` (raw motion alerts), `object_motion_person`, `object_motion_animal` (YOLO detections), `arm_disarm`, `sensor_motion` (HSS events).

**Motion detection masks.** Per-camera binary PNG masks (1920x1080, values 0/255 only) at `resources/img/cam<N>_mask.png`. White = monitored area, black = ignored. Used by both motion detection (at 480x270 downscaled) and object detection (at full resolution) to filter out irrelevant regions like neighbor yards.

## Pipeline details

**RTSP capture:** ffmpeg with VAAPI hardware decode (`-hwaccel vaapi -hwaccel_device /dev/dri/renderD128`), fps filter to 2fps, outputs BMP frames to tmpfs.

**Motion detection:** Frames resized to 480x270, converted to grayscale, masked, then processed with MOG2 background subtraction. Motion triggers are based on configurable pixel count and percentage thresholds with a lookback window.

**Video encoding:** Motion frame sequences encoded with ffmpeg x264. Adaptive preset (`medium` to `ultrafast`) based on tmpfs disk usage. Runs with `nice` to yield CPU to more important work.

**Object detection:** YOLOv8m with OpenVINO backend. ROI extraction from motion metadata to limit YOLO to the area of interest. Confidence thresholds: 0.5 for detection, 0.25 for metadata storage, per-object thresholds for notifications (0.7 person, 0.5 animals). Minimum 5 frame detections required.

## Coordinate systems

- **Motion detection space:** 480x270 (4x downscale from 1920x1080)
- **Motion metadata in .json sidecars:** 1920x1080 (scaled up by `frame.get_motion_area()`)
- **YOLO detection coordinates:** 1920x1080 (after `_map_object_coordinates`)
- **Mask PNGs:** 1920x1080

## Config

YAML configs with inheritance (`extend:` key). `APP_CONFIG` env var selects which config to load. Chain: `secrets.yaml` <- `common.yaml` <- `camera_common.yaml` <- `cam<N>.yaml` (for cameras) or `common.yaml` <- `object_detector.yaml`, etc.

## Build and deploy

```bash
# Build
cd docker && ./docker_build.sh

# Run (requires --privileged or --device /dev/dri for VAAPI GPU access)
docker run -d --name sharp_eye --privileged \
  --tmpfs /tmp \
  -v ~/data/sharp_eye:/snapshots \
  -p 8090:8080 \
  sharp_eye
```

Container uses cron to launch processes. Env vars set in .sh scripts (not inherited from Docker ENV by cron). Timezone set to Europe/Sofia.

## Telemetry

InfluxDB at 192.168.1.200:8086 for metrics. HSS zone events are recorded as data points.
