# AbletonOSC: Control Ableton Live 11+ with OSC

AbletonOSC is a MIDI remote script that provides an Open Sound Control (OSC) interface to control [Ableton Live 11+](https://www.ableton.com/en/live/). Building on ideas from the older [LiveOSC](https://github.com/hanshuebner/LiveOSC) scripts, its aim is to expose the entire [Live Object Model](https://docs.cycling74.com/max8/vignettes/live_object_model) API, providing comprehensive control over Live's control interfaces using the same naming structure and object hierarchy as LOM.

It is currently (2021-05-07) a work-in-progress, exposing a few initial APIs.

# Installation

To install the script:

 - Clone this repo, or download/unzip and rename AbletonOSC-master to AbletonOSC
 - Move the AbletonOSC folder to the MIDI Remote Scripts folder inside the Ableton application: `/Applications/Ableton Live*.app/Contents/App-Resources/MIDI Remote Scripts`
 - Restart Live
 - In `Preferences > MIDI`, add the new AbletonOSC Control Surface that should appear. Live should display a message saying "AbletonOSC: Listening for OSC on port 11000"
 - On macOS, an activity log will be created at `/tmp/abletonosc.log` 

# Usage

AbletonOSC listens for OSC messages on port **11000**, and sends replies on port **11001**. 

## Application API

| Address | Query params | Response params | Description |
| :------ | :----------- | :-------------- | :---------- |
| /live/test | | | Display a test message and sends an OSC reply |
| /live/application/get/version | | major_version, minor_version | Query Live's version |

### Application status messages

These messages are sent to the client automatically when the application state changes.

| Address | Response params | Description |
| :------ | :-------------- | :---------- |
| /live/startup | | Sent to the client application when AbletonOSC is started |

---

## Song API

| Address | Query params | Response params | Description |
| :------ | :----------- | :-------------- | :---------- |
| /live/song/start_playing | | | Start session playback |
| /live/song/stop_playing | | | Stop session playback |
| /live/song/continue_playing | | | Resume session playback |
| /live/song/stop_all_clips | | | Stop all clips from playing |
| /live/song/create_audio_track | | | Create a new audio track at the cursor |
| /live/song/create_midi_track | | | Create a new MIDI track at the cursor |
| /live/song/create_return_track | | | Create a new return track at the cursor |
| /live/song/create_scene | | | Create a new scene |
| /live/song/get/is_playing | | is_playing | Query whether the song is currently playing |
| /live/song/start_listen/is_playing | | | Start a listener that sends a notification when is_playing changes|
| /live/song/stop_listen/is_playing | | | Stop the above listener |
| /live/song/get/tempo | | tempo_bpm | Query song tempo |
| /live/song/set/tempo | tempo_bpm | | Set song tempo |
| /live/song/start_listen/tempo | | | Start a listener that sends a notification when tempo changes|
| /live/song/stop_listen/tempo | | | Stop the above listener |
| /live/song/get/metronome | | metronome_on | Query metronome on/off |
| /live/song/set/metronome  | metronome_on | | Set metronome on/off |
| /live/song/start_listen/metronome | | | Start a listener that sends a notification when metronome changes|
| /live/song/stop_listen/metronome | | | Stop the above listener |

Additional properties are exposed to `get`, `set`, `start_listen` and `stop_listen` in the same manner:
 - `arrangement_overdub`, `back_to_arranger`, `clip_trigger_quantization`, `current_song_time`, `groove_amount`, `loop`, `loop_length`, `loop_start`,  `midi_recording_quantization`, `nudge_down`, `nudge_up`, `punch_in`, `punch_out`, `record_mode`

### Song status messages

These messages are sent to the client automatically when the song state changes.

| Address | Response params | Description |
| :------ | :-------------- | :---------- |
| /live/song/beat | beat_number | Sent to the client application on each beat when the song is playing |

---

## Track API

| Address | Query params | Response params | Description |
| :------ | :----------- | :-------------- | :---------- |
| /live/track/stop_all_clips | track_id | | Stop all clips on track |
| /live/track/get/color | track_id | color | Query track color |
| /live/track/set/color | track_id, color | | Set track color |
| /live/track/get/mute | track_id | mute | Query track mute on/off |
| /live/track/set/mute | track_id, mute | | Set track mute on/off |
| /live/track/get/solo | track_id | solo | Query track solo on/off |
| /live/track/set/solo | track_id, solo | | Set track solo on/off |
| /live/track/get/name | track_id | name | Query track name |
| /live/track/set/name | track_id, name | | Set track name |
| /live/track/get/volume | track_id | volume | Query track volume |
| /live/track/set/volume | track_id, volume | | Set track volume |
| /live/track/get/panning | track_id | panning | Query track panning |
| /live/track/set/panning | track_id, panning | | Set track panning |
| /live/track/get/send | track_id, send_id | value | Query track send |
| /live/track/set/send | track_id, send_id, value | | Set track send |
| /live/track/get/clips_name | track_id | [name, ....] | Query all clip names on track  |
| /live/track/get/clips_length | track_id | [length, ...] | Query all clip lengths on track |
| /live/track/get/num_devices | track_id | num_devices | Query the number of devices on the track  |
| /live/track/get/devices/name | track_id | [name, ...] | Query all device names on track |
| /live/track/get/devices/type | track_id | [type, ...] | Query all devices types on track |
| /live/track/get/devices/class_name | track_id | [class, ...] | Query all device class names on track |

See **Device API** for details on type/class_name.
 
---
 
## Clip Slot API
 
| Address | Query params | Response params | Description |
| :------ | :----------- | :-------------- | :---------- |
| /live/clip_slot/create_clip | track_id, clip_id, length | | Create a clip in the slot |
| /live/clip_slot/delete_clip | track_id, clip_id | | Delete the clip in the slot |
| /live/clip_slot/get/has_clip | track_id, clip_id | | Query whether the slot has a clip |
| /live/clip_slot/get/has_stop_button | track_id, clip_id | has_stop_button | Query whether the slot has a stop button |
| /live/clip_slot/set/has_stop_button | track_id, clip_id, has_stop_button | | Add or remove stop button |

---

## Clip API

| Address | Query params | Response params | Description |
| :------ | :----------- | :-------------- | :---------- |
| /live/clip/fire | track_id, clip_id | | Start clip playback |
| /live/clip/stop | track_id, clip_id | | Stop clip playback |
| /live/clip/add_new_note | track_id, clip_id, pitch, start_time, duration, velocity, mute | | Add a new MIDI note to a clip. pitch is MIDI note index, start_time and duration are floats in beats, velocity is MIDI velocity index, mute is on/off  |
| /live/clip/get/color | track_id, clip_id | color | Get clip color |
| /live/clip/set/color | track_id, clip_id, color | | Set clip color |
| /live/clip/get/name | track_id, clip_id | name | Get clip name |
| /live/clip/set/name | track_id, clip_id, name | | Set clip name |
| /live/clip/get/gain | track_id, clip_id | gain | Get clip gain |
| /live/clip/set/gain | track_id, clip_id, gain | | Set clip gain |
| /live/clip/get/file_path | track_id, clip_id | file_path | Get clip file path |
| /live/clip/get/is_audio_clip | track_id, clip_id | is_audio_clip | Query whether clip is audio |
| /live/clip/get/is_midi_clip | track_id, clip_id | is_midi_clip | Query whether clip is MIDI |
| /live/clip/get/is_playing | track_id, clip_id | is_playing | Query whether clip is playing |
| /live/clip/get/is_recording | track_id, clip_id | is_recording | Query whether clip is recording |

---

## Device API

| Address | Query params | Response params | Description |
| :------ | :----------- | :-------------- | :---------- |
| /live/device/get/name | track_id, device_id | | Get device name |
| /live/device/get/class_name | track_id, device_id | | Get device class_name |
| /live/device/get/type | track_id, device_id | | Get device type |
| /live/device/get/num_parameters | track_id, device_id | num_parameters | Get the number of parameters exposed by the device |
| /live/device/get/parameters/name | track_id, device_id | [name, ...] | Get the list of parameter names exposed by the device |
| /live/device/get/parameters/value | track_id, device_id | [value, ...] | Get the device parameter values |
| /live/device/get/parameters/min | track_id, device_id | [value, ...] | Get the device parameter minimum values |
| /live/device/get/parameters/max | track_id, device_id | [value, ...] | Get the device parameter maximum values |
| /live/device/set/parameters/value | track_id, device_id, value, value ... | | Set the device parameter values |
| /live/device/get/parameter/value | track_id, device_id, parameter_id | value | Get a device parameter value |
| /live/device/set/parameter/value | track_id, device_id, parameter_id, value | | Set a device parameter value |

For devices:
 - `name` is the human-readable name
 - `type` is 0 = audio_effect, 1 = instrument, 2 = midi_effect
 - `class_name` is the Live instrument/effect name, e.g. Operator, Reverb. For external plugins and racks, can be AuPluginDevice, PluginDevice, InstrumentGroupDevice...
 
 ---
 
# Acknowledgements

Thanks to [Stu Fisher](https://github.com/stufisher/) (and other authors) for LiveOSC, the spiritual predecessor to this library. Thanks to [Julien Bayle](https://structure-void.com/ableton-live-midi-remote-scripts/#liveAPI) and [NSUSpray](https://nsuspray.github.io/Live_API_Doc/) for providing XML API docs, based on original work by [Hans Petrov](http://remotescripts.blogspot.com/p/support-files.html).
