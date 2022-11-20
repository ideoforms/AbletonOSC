# AbletonOSC: Control Ableton Live 11 with OSC

[![stability-alpha](https://img.shields.io/badge/stability-alpha-f4d03f.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#alpha)

AbletonOSC is a MIDI remote script that provides an Open Sound Control (OSC) interface to
control [Ableton Live 11](https://www.ableton.com/en/live/). Building on ideas from the
older [LiveOSC](https://github.com/hanshuebner/LiveOSC) scripts, its aim is to expose the
entire [Live Object Model](https://docs.cycling74.com/max8/vignettes/live_object_model) API
([full API docs](https://structure-void.com/PythonLiveAPI_documentation/Live11.0.xml), providing comprehensive control
over Live's control interfaces using the same naming structure and object hierarchy as LOM.

AbletonOSC is currently (2022-11-20) a work-in-progress, and APIs may be subject to change. Many major APIs are now exposed.

# Installation

To install the script:

- Clone this repo, or download/unzip and rename AbletonOSC-master to AbletonOSC
- Install it following the instructions on
  Ableton's [Installing third-party remote scripts](https://help.ableton.com/hc/en-us/articles/209072009-Installing-third-party-remote-scripts)
  doc, copying the script to:
    - **Windows**: `\Users\[username]\Documents\Ableton\User Library\Remote Scripts`
    - **macOS**: `Macintosh HD/Users/[username]/Music/Ableton/User Library/Remote Scripts`
- Restart Live
- In `Preferences > MIDI`, add the new AbletonOSC Control Surface that should appear. Live should display a message
  saying "AbletonOSC: Listening for OSC on port 11000"

Activity logs will be output to a `logs` subdirectory.

# Usage

AbletonOSC listens for OSC messages on port **11000**, and sends replies on port **11001**. Replies will be sent to the
same IP as the originating message.

## Application API

<details>
<summary><b>Documentation</b>: Application API</summary>

| Address                       | Query params | Response params              | Description                                                                      |
|:------------------------------|:-------------|:-----------------------------|:---------------------------------------------------------------------------------|
| /live/test                    |              | 'ok'                         | Display a confirmation message in Live, and sends an OSC reply to /live/test     |
| /live/application/get/version |              | major_version, minor_version | Query Live's version                                                             |
| /live/reload                  |              |                              | Initiates a live reload of the AbletonOSC server code. Used in development only. |

### Application status messages

These messages are sent to the client automatically when the application state changes.

| Address       | Response params | Description                                               |
|:--------------|:----------------|:----------------------------------------------------------|
| /live/startup |                 | Sent to the client application when AbletonOSC is started |

</details>

---

## Song API

Represents the top-level Song object. Used to start/stop playback, create/modify scenes, create/jump to cue points, and set global parameters (tempo, metronome).

<details>
<summary><b>Documentation</b>: Song API</summary>

| Address                            | Query params | Response params | Description                                                                                  |
|:-----------------------------------|:-------------|:----------------|:---------------------------------------------------------------------------------------------|
| /live/song/start_playing           |              |                 | Start session playback                                                                       |
| /live/song/stop_playing            |              |                 | Stop session playback                                                                        |
| /live/song/continue_playing        |              |                 | Resume session playback                                                                      |
| /live/song/stop_all_clips          |              |                 | Stop all clips from playing                                                                  |
| /live/song/undo                    |              |                 | Undo the last operation                                                                      |
| /live/song/redo                    |              |                 | Redo the last undone operation                                                               |
| /live/song/create_audio_track      | index        |                 | Create a new audio track at the specified index (-1 = end of list)                           |
| /live/song/create_midi_track       | index        |                 | Create a new MIDI track at the specified index (-1 = end of list)                            |
| /live/song/create_return_track     |              |                 | Create a new return track                                                                    |
| /live/song/get/num_scenes          |              | num_scenes      | Query the number of scenes                                                                   | 
| /live/song/get/num_tracks          |              | num_tracks      | Query the number of tracks                                                                   | 
| /live/song/create_scene            | index        |                 | Create a new scene at the specified index (-1 = end of list)                                 |
| /live/song/delete_scene            | scene_index  |                 | Delete a scene                                                                               |
| /live/song/delete_return_track     | track_index  |                 | Delete a return track                                                                        |
| /live/song/delete_track            | track_index  |                 | Delete a track                                                                               |
| /live/song/get/is_playing          |              | is_playing      | Query whether the song is currently playing                                                  |
| /live/song/start_listen/is_playing |              |                 | Start a listener that sends a message to `/live/song/get/is_playing` when is_playing changes |
| /live/song/stop_listen/is_playing  |              |                 | Stop the above listener                                                                      |
| /live/song/get/tempo               |              | tempo_bpm       | Query song tempo                                                                             |
| /live/song/set/tempo               | tempo_bpm    |                 | Set song tempo                                                                               |
| /live/song/start_listen/tempo      |              |                 | Start a listener that sends a to `/live/song/get/tempo` tempo changes                        |
| /live/song/stop_listen/tempo       |              |                 | Stop the above listener                                                                      |
| /live/song/get/metronome           |              | metronome_on    | Query metronome on/off                                                                       |
| /live/song/set/metronome           | metronome_on |                 | Set metronome on/off                                                                         |
| /live/song/start_listen/metronome  |              |                 | Start a listener that sends a message to `/live/song/get/metronome` when metronome changes   |
| /live/song/stop_listen/metronome   |              |                 | Stop the above listener                                                                      |
| /live/song/get/cue_points          |              | name, time, ... | Query a list of the song's cue points                                                        |
| /live/song/cue_point/jump          | cue_point    |                 | Jump to a specific cue point, by name or numeric index (based on the list of cue points)     |      

Additional properties are exposed to `get`, `set`, `start_listen` and `stop_listen` in the same manner:

- `arrangement_overdub`, `back_to_arranger`, `clip_trigger_quantization`, `current_song_time`, `groove_amount`, `loop`
  , `loop_length`, `loop_start`,  `midi_recording_quantization`, `nudge_down`, `nudge_up`, `punch_in`, `punch_out`
  , `record_mode`

For further information on these properties and their parameters, see documentation
for [Live Object Model - Song](https://docs.cycling74.com/max8/vignettes/live_object_model#Song).

### Song status messages

These messages are sent to the client automatically when the song state changes.

| Address         | Response params | Description                                                          |
|:----------------|:----------------|:---------------------------------------------------------------------|
| /live/song/beat | beat_number     | Sent to the client application on each beat when the song is playing |

</details>

---

## Track API

Represents an audio, MIDI, return or master track. Can be used to set track audio parameters (volume, panning, send, mute, solo), listen for the playing clip slot, query devices, etc. Can also be used to query clips in arrangement view.

<details>
<summary><b>Documentation</b>: Track API</summary>

| Address                                      | Query params             | Response params   | Description                                                                        |
|:---------------------------------------------|:-------------------------|:------------------|:-----------------------------------------------------------------------------------|
| /live/track/stop_all_clips                   | track_id                 |                   | Stop all clips on track                                                            |
| /live/track/get/color                        | track_id                 | color             | Query track color                                                                  |
| /live/track/set/color                        | track_id, color          |                   | Set track color                                                                    |
| /live/track/get/mute                         | track_id                 | mute              | Query track mute on/off                                                            |
| /live/track/set/mute                         | track_id, mute           |                   | Set track mute on/off                                                              |
| /live/track/get/solo                         | track_id                 | solo              | Query track solo on/off                                                            |
| /live/track/set/solo                         | track_id, solo           |                   | Set track solo on/off                                                              |
| /live/track/get/name                         | track_id                 | name              | Query track name                                                                   |
| /live/track/set/name                         | track_id, name           |                   | Set track name                                                                     |
| /live/track/get/volume                       | track_id                 | volume            | Query track volume                                                                 |
| /live/track/set/volume                       | track_id, volume         |                   | Set track volume                                                                   |
| /live/track/get/panning                      | track_id                 | panning           | Query track panning                                                                |
| /live/track/set/panning                      | track_id, panning        |                   | Set track panning                                                                  |
| /live/track/get/send                         | track_id, send_id        | value             | Query track send                                                                   |
| /live/track/set/send                         | track_id, send_id, value |                   | Set track send                                                                     |
| /live/track/get/playing_slot_index           | track_id                 | index             | Query currently-playing slot                                                       |
| /live/track/start_listen/playing_slot_index  | track_id                 | track_id, index   | Start listening to currently-playing slot. Replies include the track_id and index. |
| /live/track/stop_listen/playing_slot_index   | track_id                 |                   | Stop listening to currently-playing slot                                           |
| /live/track/get/fired_slot_index             | track_id                 | index             | Query fired slot                                                                   |
| /live/track/start_listen/fired_slot_index    | track_id                 | track_id, index   | Start listening to fired slot. Replies include the track_id and index.             |
| /live/track/stop_listen/fired_slot_index     | track_id                 |                   | Stop listening to fired slot                                                       |
| /live/track/get/clips/name                   | track_id                 | [name, ....]      | Query all clip names on track                                                      |
| /live/track/get/clips/length                 | track_id                 | [length, ...]     | Query all clip lengths on track                                                    |
| /live/track/get/arrangement_clips/name       | track_id                 | [name, ....]      | Query all arrangement view clip names on track                                     |
| /live/track/get/arrangement_clips/length     | track_id                 | [length, ...]     | Query all arrangement view clip lengths on track                                   |
| /live/track/get/arrangement_clips/start_time | track_id                 | [start_time, ...] | Query all arrangement view clip times on track                                     |
| /live/track/get/num_devices                  | track_id                 | num_devices       | Query the number of devices on the track                                           |
| /live/track/get/devices/name                 | track_id                 | [name, ...]       | Query all device names on track                                                    |
| /live/track/get/devices/type                 | track_id                 | [type, ...]       | Query all devices types on track                                                   |
| /live/track/get/devices/class_name           | track_id                 | [class, ...]      | Query all device class names on track                                              |

See **Device API** for details on Device type/class_names.
 
</details>

---

## Clip Slot API

A Clip Slot represents a container for a clip. It is used to create and delete clips, and query their existence.

<details>
<summary><b>Documentation</b>: Clip Slot API</summary>

| Address                             | Query params                       | Response params | Description                              |
|:------------------------------------|:-----------------------------------|:----------------|:-----------------------------------------|
| /live/clip_slot/create_clip         | track_id, clip_id, length          |                 | Create a clip in the slot                |
| /live/clip_slot/delete_clip         | track_id, clip_id                  |                 | Delete the clip in the slot              |
| /live/clip_slot/get/has_clip        | track_id, clip_id                  |                 | Query whether the slot has a clip        |
| /live/clip_slot/get/has_stop_button | track_id, clip_id                  | has_stop_button | Query whether the slot has a stop button |
| /live/clip_slot/set/has_stop_button | track_id, clip_id, has_stop_button |                 | Add or remove stop button                |

# TODO: Add more properties and methods

</details>

---

## Clip API

Represents an audio or MIDI clip. Can be used to start/stop clips, and query/modify their notes, name, gain, pitch, color, playing state/position, etc.

<details>
<summary><b>Documentation</b>: Clip API</summary>

| Address                                  | Query params                                                        | Response params                                                     | Description                                                                                                                                          |
|:-----------------------------------------|:--------------------------------------------------------------------|:--------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|
| /live/clip/fire                          | track_id, clip_id                                                   |                                                                     | Start clip playback                                                                                                                                  |
| /live/clip/stop                          | track_id, clip_id                                                   |                                                                     | Stop clip playback                                                                                                                                   |
| /live/clip/get/notes                     | track_id, clip_id                                                   | pitch, start_time, duration, velocity, mute, [pitch, start_time...] | Query the notes in a given clip.                                                                                                                     |
| /live/clip/add/notes                     | track_id, clip_id, pitch, start_time, duration, velocity, mute, ... |                                                                     | Add new MIDI notes to a clip. pitch is MIDI note index, start_time and duration are beats in floats, velocity is MIDI velocity index, mute is on/off |
| /live/clip/remove/notes                  | start_pitch, pitch_span, start_time, time_span                      |                                                                     | Remove notes from a clip in a given range of pitches and times.                                                                                      |
| /live/clip/get/color                     | track_id, clip_id                                                   | color                                                               | Get clip color                                                                                                                                       |
| /live/clip/set/color                     | track_id, clip_id, color                                            |                                                                     | Set clip color                                                                                                                                       |
| /live/clip/get/name                      | track_id, clip_id                                                   | name                                                                | Get clip name                                                                                                                                        |
| /live/clip/set/name                      | track_id, clip_id, name                                             |                                                                     | Set clip name                                                                                                                                        |
| /live/clip/get/gain                      | track_id, clip_id                                                   | gain                                                                | Get clip gain                                                                                                                                        |
| /live/clip/set/gain                      | track_id, clip_id, gain                                             |                                                                     | Set clip gain                                                                                                                                        |
| /live/clip/get/length                    | track_id, clip_id                                                   | length                                                              | Get clip length                                                                                                                                      |
| /live/clip/get/pitch_coarse              | track_id, clip_id                                                   | semitones                                                           | Get clip coarse re-pitch                                                                                                                             |
| /live/clip/set/pitch_coarse              | track_id, clip_id, semitones                                        |                                                                     | Set clip coarse re-pitch                                                                                                                             |
| /live/clip/get/pitch_fine                | track_id, clip_id                                                   | cents                                                               | Get clip fine re-pitch                                                                                                                               |
| /live/clip/set/pitch_fine                | track_id, clip_id, cents                                            |                                                                     | Set clip fine re-pitch                                                                                                                               |
| /live/clip/get/file_path                 | track_id, clip_id                                                   | file_path                                                           | Get clip file path                                                                                                                                   |
| /live/clip/get/is_audio_clip             | track_id, clip_id                                                   | is_audio_clip                                                       | Query whether clip is audio                                                                                                                          |
| /live/clip/get/is_midi_clip              | track_id, clip_id                                                   | is_midi_clip                                                        | Query whether clip is MIDI                                                                                                                           |
| /live/clip/get/is_playing                | track_id, clip_id                                                   | is_playing                                                          | Query whether clip is playing                                                                                                                        |
| /live/clip/get/is_recording              | track_id, clip_id                                                   | is_recording                                                        | Query whether clip is recording                                                                                                                      |
| /live/clip/get/playing_position          | track_id, clip_id                                                   | playing_position                                                    | Get clip's playing position                                                                                                                          |
| /live/clip/start_listen/playing_position | track_id, clip_id                                                   |                                                                     | Start listening for clip's playing position. Replies are sent to /live/clip/get/playing_position, with args: track_id, clip_id, playing_position     |
| /live/clip/stop_listen/playing_position  | track_id, clip_id                                                   |                                                                     | Stop listening for clip's playing position.                                                                                                          |
</details>

---

## Device API

Represents an instrument or effect.

<details>
<summary><b>Documentation</b>: Device API</summary>

| Address                           | Query params                             | Response params | Description                                           |
|:----------------------------------|:-----------------------------------------|:----------------|:------------------------------------------------------|
| /live/device/get/name             | track_id, device_id                      |                 | Get device name                                       |
| /live/device/get/class_name       | track_id, device_id                      |                 | Get device class_name                                 |
| /live/device/get/type             | track_id, device_id                      |                 | Get device type                                       |
| /live/device/get/num_parameters   | track_id, device_id                      | num_parameters  | Get the number of parameters exposed by the device    |
| /live/device/get/parameters/name  | track_id, device_id                      | [name, ...]     | Get the list of parameter names exposed by the device |
| /live/device/get/parameters/value | track_id, device_id                      | [value, ...]    | Get the device parameter values                       |
| /live/device/get/parameters/min   | track_id, device_id                      | [value, ...]    | Get the device parameter minimum values               |
| /live/device/get/parameters/max   | track_id, device_id                      | [value, ...]    | Get the device parameter maximum values               |
| /live/device/set/parameters/value | track_id, device_id, value, value ...    |                 | Set the device parameter values                       |
| /live/device/get/parameter/value  | track_id, device_id, parameter_id        | value           | Get a device parameter value                          |
| /live/device/set/parameter/value  | track_id, device_id, parameter_id, value |                 | Set a device parameter value                          |

For devices:

- `name` is the human-readable name
- `type` is 0 = audio_effect, 1 = instrument, 2 = midi_effect
- `class_name` is the Live instrument/effect name, e.g. Operator, Reverb. For external plugins and racks, can be
  AuPluginDevice, PluginDevice, InstrumentGroupDevice...

</details>

 ---

# Acknowledgements

Thanks to [Stu Fisher](https://github.com/stufisher/) (and other authors) for LiveOSC, the spiritual predecessor to this
library. Thanks to [Julien Bayle](https://structure-void.com/ableton-live-midi-remote-scripts/#liveAPI)
and [NSUSpray](https://nsuspray.github.io/Live_API_Doc/) for providing XML API docs, based on original work
by [Hans Petrov](http://remotescripts.blogspot.com/p/support-files.html).
