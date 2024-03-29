# Sharp eye v2

## Summary

Sharp eye is a custom surveillance system. It captures RTSP output of IP camera, detect motion, generate motion videos
and performs object detection in the motion videos. The system send notifications for motions and detected objects.

Runs in a Docker container on x86 machine.

This is V2. V1 is available [here](github.com/funnybrum/sharp_eye). It was running on Raspberry Pi 2 and was designed
for constrained system resources.

V2 has upgrades that enable better motion detection logic, motion is captured in video now. The videos are then
processed through ML model (YOLO v7) to identify objects in them. Based on the detected motion and objects the system
generates notifications.

V2 has been extended to expose control over the Security System that I'm using from Paradox. The UI allows users to arm
or disarm zones.

## Architecture
The application is running inside an Ubnutu based Docker container. There are multiple Python3 processes running inside:
  * One for the Sharp Eye web based UI
  * One for each attached camera
  * One for generating notifications based on the events coming from the Security System
  * One for running ML model on the detected motion videos for detecting objects in them

## Requirements
* WiFi cameras that can provide snapshots.
* External notification service to enable notification processing (not publicly available currently).
* Average x86 CPU (runs fine on i5-8500T with 5 cameras and 2FPS).

## Settings
Note: This section is outdated. It will be updated in the future.
### Admin interface
The settings are in `./resources/admin.yaml`.

The Admin interface runs over HTTP. 


HTTPS is also supported. If required - provide a certificate and key file in PEM format. Put them in `./resources/key.pem` and `./resources/cert.pem`. Update the config - ssl_cert, ssl_key, ss_pass.

An additional password for accessing the Admin UI should be provided.

An array of cameras is also provided. This tells the UI which are the cameras and how to start the motion detection processes for them.

### Camera
The camera config provides the URI of the video stream and snapshot location details. A common motion detection configuration is provided tool.

The camera configuration resides in the following files:

* camX_mask.png - a black and white motion detection mask. A black area in that mask indicates that no motion detection is performed for that area.
* camX.yaml - the camera settings.
* common.yaml - common settings for all cameras (email account settings and credentials).

Check the camX.yaml as start. Most of the required details are there.

The common.yaml should provide all required details for the emails. The following details should be provided:

* SET_TO_EMAIL_HERE - the email where motion detection notifications will be send.
* SET_FROM_EMAIL_HERE - the email where the motion detection emails will be coming from.
* GMAIL_ACCOUNT_USERNAME/GMAIL_ACCOUNT_PASSWORD - credentials for a gmail.com account. The account should allow simple SMTP authentication (this was a setting somewhere in the account).

## Running the surveillance system
Build the docker container image (./docker/docker_build.sh) and run it:
`docker run -d --name=sharp_eye -p 192.168.0.200:8080:8080 --tmpfs /tmp sharp_eye`

Note that the /tmp folder by default is set for keeping the snapshots too. It is recommended to reconfigure the snapshot history location () and put it on a permanent storage. The snapshot history location is provided in the config files - `snapshot_history_location`.

It will take up to a minute for the process to start (each round minute a verification is performed to confirm the process is up and running). Once the Admin process is started open the UI and check if the interface is working. If so - you'll be able to see up-to-date snapshots when pressing the snapshot buttons for each of the cameras.

## Tweaking motion detection settings
There are Python scripts in the src/tests folder that can help with that. The process for this is:
1) Capture a lot of snapshots (let's say fo a single day) by setting `snapshot_history` to `full`
2) Manually validate which snapshots contain motion that should be detected and store the info in metadata files
3) Run the motion_verifier.py and check the results.