# AbletonOSC: Control Ableton Live 11 with OSC

[![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta)

AbletonOSC is a MIDI remote script that provides an Open Sound Control (OSC) interface to
control [Ableton Live 11](https://www.ableton.com/en/live/). Building on ideas from the
older [LiveOSC](https://github.com/hanshuebner/LiveOSC) scripts, its aim is to expose the
entire [Live Object Model](https://docs.cycling74.com/max8/vignettes/live_object_model) API
([full API docs](https://structure-void.com/PythonLiveAPI_documentation/Live11.0.xml)), providing comprehensive control
over Live's control interfaces using the same naming structure and object hierarchy as LOM.

**NOTE: Since 2022-12-17, all getters have been modified to return the ID of the object being queried as well as the return value**, for consistency with listeners. For example, `/live/clip/get/name` will return `track_id, clip_id, name`.

# Installation

AbletonOSC requires Ableton Live 11 or above, and does not support earlier versions.

To install the script:

- [Download a zip of this repository](https://github.com/ideoforms/AbletonOSC/archive/refs/heads/master.zip), unzip its contents, and rename `AbletonOSC-master` to `AbletonOSC`
- Install it following the instructions on
  Ableton's [Installing third-party remote scripts](https://help.ableton.com/hc/en-us/articles/209072009-Installing-third-party-remote-scripts)
  doc, by copying the `AbletonOSC` folder to:
    - **Windows**: `\Users\[username]\Documents\Ableton\User Library\Remote Scripts`
    - **macOS**: `Macintosh HD/Users/[username]/Music/Ableton/User Library/Remote Scripts`
- Restart Live
- In `Preferences > Link / Tempo / MIDI`, under the Control Surface dropdown, select the new "AbletonOSC" option. Live should display a message
  saying "AbletonOSC: Listening for OSC on port 11000"

Activity logs will be output to a `logs` subdirectory. Logging granularity can be controlled with `/live/api/set/log_level` (see [Application API](#application-api) below). 

# Usage

AbletonOSC listens for OSC messages on port **11000**, and sends replies on port **11001**. Replies will be sent to the
same IP as the originating message. When querying properties, OSC wildcard patterns can be used; for example, `/live/clip/get/* 0 0` will query all the properties of track 0, clip 0.

## Application API

<details>
<summary><b>Documentation</b>: Application API</summary>

| Address                       | Query params | Response params              | Description                                                                              |
|:------------------------------|:-------------|:-----------------------------|:-----------------------------------------------------------------------------------------|
| /live/test                    |              | 'ok'                         | Display a confirmation message in Live, and sends an OSC reply to /live/test             |
| /live/application/get/version |              | major_version, minor_version | Query Live's version                                                                     |
| /live/api/reload              |              |                              | Initiates a live reload of the AbletonOSC server code. Used in development only.         |
| /live/api/get/log_level       |              | log_level                    | Returns the current log level. Default is `info`.                                        |
| /live/api/set/log_level       | log_level    |                              | Set the log level, which can be one of: `debug`, `info`, `warning`, `error`, `critical`. |

### Application status messages

These messages are sent to the client automatically when the application state changes.

| Address       | Response params | Description                                                                                        |
|:--------------|:----------------|:---------------------------------------------------------------------------------------------------|
| /live/startup |                 | Sent to the client application when AbletonOSC is started                                          |
| /live/error   | error_msg       | Sent to the client application when an error occurs. For more diagnostics, see logs/abletonosc.log |

</details>

---

## Song API

Represents the top-level Song object. Used to start/stop playback, create/modify scenes, create/jump to cue points, and set global parameters (tempo, metronome).

<details>
<summary><b>Documentation</b>: Song API</summary>

### Song methods

| Address                           | Query params | Response params | Description                                                                              |
|:----------------------------------|:-------------|:----------------|:-----------------------------------------------------------------------------------------|
| /live/song/capture_midi           |              |                 | Capture midi                                                                             |
| /live/song/continue_playing       |              |                 | Resume session playback                                                                  |
| /live/song/create_audio_track     | index        |                 | Create a new audio track at the specified index (-1 = end of list)                       |
| /live/song/create_midi_track      | index        |                 | Create a new MIDI track at the specified index (-1 = end of list)                        |
| /live/song/create_return_track    |              |                 | Create a new return track                                                                |
| /live/song/create_scene           | index        |                 | Create a new scene at the specified index (-1 = end of list)                             |
| /live/song/cue_point/jump         | cue_point    |                 | Jump to a specific cue point, by name or numeric index (based on the list of cue points) |
| /live/song/delete_scene           | scene_index  |                 | Delete a scene                                                                           |
| /live/song/delete_return_track    | track_index  |                 | Delete a return track                                                                    |
| /live/song/delete_track           | track_index  |                 | Delete a track                                                                           |
| /live/song/duplicate_scene        | scene_index  |                 | Duplicate a scene                                                                        |
| /live/song/duplicate_track        | track_index  |                 | Duplicate a track                                                                        |
| /live/song/jump_by                | time         |                 | Jump song position by the specified time, in beats                                       |
| /live/song/jump_to_next_cue       |              |                 | Jump to the next cue marker                                                              |
| /live/song/jump_to_prev_cue       |              |                 | Jump to the previous cue marker                                                          |
| /live/song/redo                   |              |                 | Redo the last undone operation                                                           |
| /live/song/start_playing          |              |                 | Start session playback                                                                   |
| /live/song/stop_playing           |              |                 | Stop session playback                                                                    |
| /live/song/stop_all_clips         |              |                 | Stop all clips from playing                                                              |
| /live/song/tap_tempo              |              |                 | Mimics a tap of the "Tap Tempo" button                                                   |
| /live/song/trigger_session_record |              |                 | Triggers record in session mode                                                          |
| /live/song/undo                   |              |                 | Undo the last operation                                                                  |

### Song properties

 - Changes to any Track property can be listened for by calling `/live/song/start_listen/<property>`
 - Responses will be sent to `/live/song/get/<property>`, with parameters `<property_value>`
 - For further information on these properties and their parameters, see documentation
for [Live Object Model - Song](https://docs.cycling74.com/max8/vignettes/live_object_model#Song).
 
#### Getters

| Address                                    | Query params | Response params             | Description                                       |
|:-------------------------------------------|:-------------|:----------------------------|:--------------------------------------------------|
| /live/song/get/arrangement_overdub         |              | arrangement_overdub         | Query whether arrangement overdub is on           |
| /live/song/get/back_to_arranger            |              | back_to_arranger            | Query whether "back to arranger" is lit           |
| /live/song/get/can_redo                    |              | can_redo                    | Query whether redo is available                   |
| /live/song/get/can_undo                    |              | can_undo                    | Query whether undo is available                   |
| /live/song/get/clip_trigger_quantization   |              | clip_trigger_quantization   | Query the current clip trigger quantization level |
| /live/song/get/current_song_time           |              | current_song_time           | Query the current song time, in beats             |
| /live/song/get/groove_amount               |              | groove_amount               | Query the current groove amount                   |
| /live/song/get/is_playing                  |              | is_playing                  | Query whether the song is currently playing       |
| /live/song/get/loop                        |              | loop                        | Query whether the song is currently looping       |
| /live/song/get/loop_length                 |              | loop_length                 | Query the current loop length                     |
| /live/song/get/loop_start                  |              | loop_start                  | Query the current loop start point                |
| /live/song/get/metronome                   |              | metronome_on                | Query metronome on/off                            |
| /live/song/get/midi_recording_quantization |              | midi_recording_quantization | Query the current MIDI recording quantization     |
| /live/song/get/nudge_down                  |              | nudge_down                  | Query nudge down                                  |
| /live/song/get/nudge_up                    |              | nudge_up                    | Query nudge up                                    |
| /live/song/get/punch_in                    |              | punch_in                    | Query punch in                                    |
| /live/song/get/punch_out                   |              | punch_out                   | Query punch out                                   |
| /live/song/get/record_mode                 |              | record_mode                 | Query the current record mode                     |
| /live/song/get/session_record              |              | session_record              | Query whether session record is enabled           |
| /live/song/get/signature_denominator       |              | denominator                 | Query the current time signature's denominator    |
| /live/song/get/signature_numerator         |              | numerator                   | Query the current time signature's numerator      |
| /live/song/get/song_length                 |              | song_length                 | Query the song arrangement length, in beats       |
| /live/song/get/tempo                       |              | tempo_bpm                   | Query the current song tempo                      |

#### Setters

| Address                                    | Query params                | Response params | Description                                             |
|:-------------------------------------------|:----------------------------|:----------------|:--------------------------------------------------------|
| /live/song/set/arrangement_overdub         | arrangement_overdub         |                 | Set arrangement overdub (1=on, 0=off)                   |
| /live/song/set/back_to_arranger            | back_to_arranger            |                 | Set whether "back to arranger" is lit (1=on, 0=off)     |
| /live/song/set/clip_trigger_quantization   | clip_trigger_quantization   |                 | Set the current clip trigger quantization level         |
| /live/song/set/current_song_time           | current_song_time           |                 | Set the current song time, in beats                     |
| /live/song/set/groove_amount               | groove_amount               |                 | Set the current groove amount                           |
| /live/song/set/loop                        | loop                        |                 | Set whether the song is currently looping (1=on, 0=off) |
| /live/song/set/loop_length                 | loop_length                 |                 | Set the current loop length                             |
| /live/song/set/loop_start                  | loop_start                  |                 | Set the current loop start point                        |
| /live/song/set/metronome                   | metronome_on                |                 | Set metronome (1=on, 0=off)                             |
| /live/song/set/midi_recording_quantization | midi_recording_quantization |                 | Set the current MIDI recording quantization             |
| /live/song/set/nudge_down                  | nudge_down                  |                 | Set nudge down                                          |
| /live/song/set/nudge_up                    | nudge_up                    |                 | Set nudge up                                            |
| /live/song/set/punch_in                    | punch_in                    |                 | Set punch in                                            |
| /live/song/set/punch_out                   | punch_out                   |                 | Set punch out                                           |
| /live/song/set/record_mode                 | record_mode                 |                 | Set the current record mode                             |
| /live/song/set/session_record              | session_record              |                 | Set whether session record is enabled (1=on, 0=off)     |
| /live/song/set/signature_denominator       | signature_denominator       |                 | Set the time signature's denominator                    |
| /live/song/set/signature_numerator         | signature_numerator         |                 | Set the time signature's numerator                      |
| /live/song/set/record_mode                 | record_mode                 |                 | Set the current record mode                             |
| /live/song/set/tempo                       | tempo_bpm                   |                 | Set the current song tempo                              |

### Song: Properties of cue points, scenes and tracks

| Address                    | Query params | Response params        | Description                                                                 |
|:---------------------------|:-------------|:-----------------------|:----------------------------------------------------------------------------|
| /live/song/get/cue_points  |              | name, time, ...        | Query a list of the song's cue points                                       |
| /live/song/get/num_scenes  |              | num_scenes             | Query the number of scenes                                                  |
| /live/song/get/num_tracks  |              | num_tracks             | Query the number of tracks                                                  |
| /live/song/get/track_names |              | [index_min, index_max] | Query track names (optionally, over a given range)                          |
| /live/song/get/track_data  |              | [various]              | Query bulk properties of multiple tracks/clips. See below for further info. |


#### Querying track/clip data in bulk with /live/song/get/track_data

It is often useful to be able to query data en masse about lots of different tracks and clips -- for example, when a set is first opened, to synchronise the state of your client with the Ableton set. This can be achieved with the `/live/song/get/track_data` API, which can query user-specified properties of multiple tracks and clips.

Properties must be of the format `track.property_name`, `clip.property_name` or `clip_slot.property_name`.

For example:
```
/live/song/get/track_data 0 12 track.name clip.name clip.length
```

Queries tracks 0..11, and returns a long list of values comprising:

```
[track_0_name, clip_0_0_name,   clip_0_1_name,   ... clip_0_7_name,
               clip_1_0_length, clip_0_1_length, ... clip_0_7_length,
 track_1_name, clip_1_0_name,   clip_1_1_name,   ... clip_1_7_name, ...]
```

### Beat events

To request a status message to be sent to the client on each beat, call `/live/song/start_listen/beat`. Every beat, a reply will be sent to `/live/song/get/beat`, with an int parameter containing the current beat number. To stop listening for beat events, call `/live/song/stop_listen/beat`.

</details>

---

## View API

Represents the view (user interface) of live

<details>
<summary><b>Documentation</b>: View API</summary>

| Address                                | Query params             | Response params          | Description                                             |
|:---------------------------------------|:-------------------------|:-------------------------|:--------------------------------------------------------|
| /live/view/get/selected_scene          |                          | scene_index              | Returns the selected scene index (first scene = 0)      |
| /live/view/get/selected_track          |                          | track_index              | Returns the selected index track (first track = 0)      |
| /live/view/get/selected_clip           |                          | track_index, scene_index | Returns the track and scene index of the selected clip  |
| /live/view/get/selected_device         |                          | track_index, device_index| Get the selected device (first device = 0)              |
| /live/view/set/selected_scene          | scene_index              |                          | Set the selected scene (first scene = 0)                |
| /live/view/set/selected_track          | track_index              |                          | Set the selected track (first track = 0)                |
| /live/view/set/selected_clip           | track_index, scene_index |                          | Set the selected clip                                   |
| /live/view/set/selected_device         | track_index, device_index|                          | Set the selected device (first device = 0)              |
| /live/view/start_listen/selected_scene |                          | selected_scene           | Start listening to the selected scene (first scene = 0) |
| /live/view/start_listen/selected_track |                          | selected_track           | Start listening to selected track (first track = 0)     |
| /live/view/stop_listen/selected_scene  |                          |                          | Stop listening to the selected scene (first scene = 0)  |
| /live/view/stop_listen/selected_track  |                          |                          | Stop listening to selected track (first track = 0)      |
</details>

---

## Track API

Represents an audio, MIDI, return or master track. Can be used to set track audio parameters (volume, panning, send, mute, solo), listen for the playing clip slot, query devices, etc. Can also be used to query clips in arrangement view.

To query the properties of multiple tracks, see [Song: Properties of cue points, scenes and tracks](https://github.com/ideoforms/AbletonOSC#song-properties-of-cue-points-scenes-and-tracks).

<details>
<summary><b>Documentation</b>: Track API</summary>

### Track methods

| Address                    | Query params | Response params | Description             |
|:---------------------------|:-------------|:----------------|:------------------------|
| /live/track/stop_all_clips | track_id     |                 | Stop all clips on track |

### Track properties

 - Changes for any Track property can be listened for by calling `/live/track/start_listen/<property> <track_index>`
 - Responses will be sent to `/live/track/get/<property>`, with parameters `<track_index> <property_value>`

#### Getters

| Address                                           | Query params      | Response params            | Description                                       |
|:--------------------------------------------------|:------------------|:---------------------------|:--------------------------------------------------|
| /live/track/get/arm                               | track_id          | track_id, armed            | Query whether track is armed                      |
| /live/track/get/available_input_routing_channels  | track_id          | track_id, channel, ...     | List input channels (e.g. "1", "2", "1/2", ...)   |
| /live/track/get/available_input_routing_types     | track_id          | track_id, type, ...        | List input routes (e.g. "Ext. In", ...)           |
| /live/track/get/available_output_routing_channels | track_id          | track_id, channel, ...     | List output channels (e.g. "1", "2", "1/2", ...)  |
| /live/track/get/available_output_routing_types    | track_id          | track_id, type, ...        | List output routes (e.g. "Ext. Out", ...)         |
| /live/track/get/can_be_armed                      | track_id          | track_id, can_be_armed     | Query whether track can be armed                  |
| /live/track/get/color                             | track_id          | track_id, color            | Query track color                                 |
| /live/track/get/color_index                       | track_id          | track_id, color_index      | Query track color index                           |
| /live/track/get/current_monitoring_state          | track_id          | track_id, state            | Query current monitoring state (1=on, 0=off)      |
| /live/track/get/fired_slot_index                  | track_id          | track_id, index            | Query currently-fired slot                        |
| /live/track/get/fold_state                        | track_id          | track_id, fold_state       | Query folded state (for groups)                   |
| /live/track/get/has_audio_input                   | track_id          | track_id, has_audio_input  | Query has_audio_input                             |
| /live/track/get/has_audio_output                  | track_id          | track_id, has_audio_output | Query has_audio_output                            |
| /live/track/get/has_midi_input                    | track_id          | track_id, has_midi_input   | Query has_midi_input                              |
| /live/track/get/has_midi_output                   | track_id          | track_id, has_midi_output  | Query has_midi_output                             |
| /live/track/get/input_routing_channel             | track_id          | track_id, channel          | Query current input routing channel               |
| /live/track/get/input_routing_type                | track_id          | track_id, type             | Query current input routing type                  |
| /live/track/get/output_routing_channel            | track_id          | track_id, channel          | Query current output routing channel              |
| /live/track/get/output_meter_left                 | track_id          | track_id, level            | Query current output level, left channel          |
| /live/track/get/output_meter_level                | track_id          | track_id, level            | Query current output level, both channels         |
| /live/track/get/output_meter_right                | track_id          | track_id, level            | Query current output level, right channel         |
| /live/track/get/output_routing_type               | track_id          | track_id, type             | Query current output routing type                 |
| /live/track/get/is_foldable                       | track_id          | track_id, is_foldable      | Query whether track is foldable, i.e. is a group  |
| /live/track/get/is_grouped                        | track_id          | track_id, is_grouped       | Query whether track is in a group                 |
| /live/track/get/is_visible                        | track_id          | track_id, is_visible       | Query whether track is visible (1=on, 0=off)      |
| /live/track/get/mute                              | track_id          | track_id, mute             | Query track mute (1=on, 0=off)                    |
| /live/track/get/name                              | track_id          | track_id, name             | Query track name                                  |
| /live/track/get/panning                           | track_id          | track_id, panning          | Query track panning                               |
| /live/track/get/playing_slot_index                | track_id          | track_id, index            | Query currently-playing slot                      |
| /live/track/get/send                              | track_id, send_id | track_id, send_id, value   | Query track send                                  |
| /live/track/get/solo                              | track_id          | track_id, solo             | Query track solo on/off                           |
| /live/track/get/volume                            | track_id          | track_id, volume           | Query track volume                                |

#### Setters

| Address                                  | Query params             | Response params | Description                       |
|:-----------------------------------------|:-------------------------|:----------------|:----------------------------------|
| /live/track/set/arm                      | track_id, armed          |                 | Set track arm state (1=on, 0=off) |
| /live/track/set/color                    | track_id, color          |                 | Set track color                   |
| /live/track/set/color_index              | track_id, color_index    |                 | Set track color index             |
| /live/track/set/current_monitoring_state | track_id, state          |                 | Set monitoring on/off             |
| /live/track/set/fold_state               | track_id, fold_state     |                 | Set group folded (1=on, 0=off)    |
| /live/track/set/input_routing_channel    | track_id, channel        |                 | Set input routing channel         |
| /live/track/set/input_routing_type       | track_id, type           |                 | Set input routing type            |
| /live/track/set/mute                     | track_id, mute           |                 | Set track mute (1=on, 0=off)      |
| /live/track/set/name                     | track_id, name           |                 | Set track name                    |
| /live/track/set/output_routing_channel   | track_id, channel        |                 | Set output routing channel        |
| /live/track/set/output_routing_type      | track_id, type           |                 | Set output routing type           |
| /live/track/set/panning                  | track_id, panning        |                 | Set track panning                 |
| /live/track/set/send                     | track_id, send_id, value |                 | Set track send                    |
| /live/track/set/solo                     | track_id, solo           |                 | Set track solo (1=on, 0=off)      |
| /live/track/set/volume                   | track_id, volume         |                 | Set track volume                  |

### Track: Properties of multiple clips

| Address                                      | Query params | Response params             | Description                                      |
|:---------------------------------------------|:-------------|:----------------------------|:-------------------------------------------------|
| /live/track/get/clips/name                   | track_id     | track_id, [name, ....]      | Query all clip names on track                    |
| /live/track/get/clips/length                 | track_id     | track_id, [length, ...]     | Query all clip lengths on track                  |
| /live/track/get/clips/color                  | track_id     | track_id, [color, ...]      | Query all clip colors on track                   |
| /live/track/get/arrangement_clips/name       | track_id     | track_id, [name, ....]      | Query all arrangement view clip names on track   |
| /live/track/get/arrangement_clips/length     | track_id     | track_id, [length, ...]     | Query all arrangement view clip lengths on track |
| /live/track/get/arrangement_clips/start_time | track_id     | track_id, [start_time, ...] | Query all arrangement view clip times on track   |

### Track: Properties of devices
| Address                            | Query params | Response params        | Description                              |
|:-----------------------------------|:-------------|:-----------------------|:-----------------------------------------|
| /live/track/get/num_devices        | track_id     | track_id, num_devices  | Query the number of devices on the track |
| /live/track/get/devices/name       | track_id     | track_id, [name, ...]  | Query all device names on track          |
| /live/track/get/devices/type       | track_id     | track_id, [type, ...]  | Query all devices types on track         |
| /live/track/get/devices/class_name | track_id     | track_id, [class, ...] | Query all device class names on track    |

See [Device API](#device-api) for details on Device type/class_names.
 
</details>

---

## Clip Slot API

A Clip Slot represents a container for a clip. It is used to create and delete clips, and query their existence.

<details>
<summary><b>Documentation</b>: Clip Slot API</summary>

| Address                             | Query params                                                   | Response params                          | Description                                     |
|:------------------------------------|:---------------------------------------------------------------|:-----------------------------------------|:------------------------------------------------|
| /live/clip_slot/create_clip         | track_index, clip_index, length                                |                                          | Create a clip in the slot                       |
| /live/clip_slot/delete_clip         | track_index, clip_index                                        |                                          | Delete the clip in the slot                     |
| /live/clip_slot/get/has_clip        | track_index, clip_index                                        | track_index, clip_index, has_clip        | Query whether the slot has a clip               |
| /live/clip_slot/get/has_stop_button | track_index, clip_index                                        | track_index, clip_index, has_stop_button | Query whether the slot has a stop button        |
| /live/clip_slot/set/has_stop_button | track_index, clip_index, has_stop_button                       |                                          | Add or remove stop button (1=on, 0=off)         |
| /live/clip_slot/duplicate_clip_to   | track_index, clip_index, target_track_index, target_clip_index |                                          | Duplicate the clip to an empty target clip slot |

</details>

---

## Clip API

Represents an audio or MIDI clip. Can be used to start/stop clips, and query/modify their notes, name, gain, pitch, color, playing state/position, etc.

<details>
<summary><b>Documentation</b>: Clip API</summary>

| Address                                  | Query params                                                        | Response params                                                                        | Description                                                                                                                                              |
|:-----------------------------------------|:--------------------------------------------------------------------|:---------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------|
| /live/clip/fire                          | track_id, clip_id                                                   |                                                                                        | Start clip playback                                                                                                                                      |
| /live/clip/stop                          | track_id, clip_id                                                   |                                                                                        | Stop clip playback                                                                                                                                       |
| /live/clip/duplicate_loop                | track_id, clip_id                                                   |                                                                                        | Duplicates clip loop                                                                                                                                     |
| /live/clip/get/notes                     | track_id, clip_id, [start_pitch, pitch_span, start_time, time_span] | track_id, clip_id, pitch, start_time, duration, velocity, mute, [pitch, start_time...] | Query the notes in a given clip, optionally including a start time/pitch and time/pitch span.                                                            |
| /live/clip/add/notes                     | track_id, clip_id, pitch, start_time, duration, velocity, mute, ... |                                                                                        | Add new MIDI notes to a clip. pitch is MIDI note index, start_time and duration are beats in floats, velocity is MIDI velocity index, mute is true/false |
| /live/clip/remove/notes                  | [start_pitch, pitch_span, start_time, time_span]                    |                                                                                        | Remove notes from a clip in a range of pitches and times. If no ranges specified, all notes are removed. Note that ordering has changed as of 2023-11.   |
| /live/clip/get/color                     | track_id, clip_id                                                   | track_id, clip_id, color                                                               | Get clip color                                                                                                                                           |
| /live/clip/set/color                     | track_id, clip_id, color                                            |                                                                                        | Set clip color                                                                                                                                           |
| /live/clip/get/name                      | track_id, clip_id                                                   | track_id, clip_id, name                                                                | Get clip name                                                                                                                                            |
| /live/clip/set/name                      | track_id, clip_id, name                                             |                                                                                        | Set clip name                                                                                                                                            |
| /live/clip/get/gain                      | track_id, clip_id                                                   | track_id, clip_id, gain                                                                | Get clip gain                                                                                                                                            |
| /live/clip/set/gain                      | track_id, clip_id, gain                                             |                                                                                        | Set clip gain                                                                                                                                            |
| /live/clip/get/length                    | track_id, clip_id                                                   | track_id, clip_id, length                                                              | Get clip length                                                                                                                                          |
| /live/clip/get/pitch_coarse              | track_id, clip_id                                                   | track_id, clip_id, semitones                                                           | Get clip coarse re-pitch                                                                                                                                 |
| /live/clip/set/pitch_coarse              | track_id, clip_id, semitones                                        |                                                                                        | Set clip coarse re-pitch                                                                                                                                 |
| /live/clip/get/pitch_fine                | track_id, clip_id                                                   | track_id, clip_id, cents                                                               | Get clip fine re-pitch                                                                                                                                   |
| /live/clip/set/pitch_fine                | track_id, clip_id, cents                                            |                                                                                        | Set clip fine re-pitch                                                                                                                                   |
| /live/clip/get/file_path                 | track_id, clip_id                                                   | track_id, clip_id, file_path                                                           | Get clip file path                                                                                                                                       |
| /live/clip/get/is_audio_clip             | track_id, clip_id                                                   | track_id, clip_id, is_audio_clip                                                       | Query whether clip is audio                                                                                                                              |
| /live/clip/get/is_midi_clip              | track_id, clip_id                                                   | track_id, clip_id, is_midi_clip                                                        | Query whether clip is MIDI                                                                                                                               |
| /live/clip/get/is_playing                | track_id, clip_id                                                   | track_id, clip_id, is_playing                                                          | Query whether clip is playing                                                                                                                            |
| /live/clip/get/is_recording              | track_id, clip_id                                                   | track_id, clip_id, is_recording                                                        | Query whether clip is recording                                                                                                                          |
| /live/clip/get/playing_position          | track_id, clip_id                                                   | track_id, clip_id, playing_position                                                    | Get clip's playing position                                                                                                                              |
| /live/clip/start_listen/playing_position | track_id, clip_id                                                   |                                                                                        | Start listening for clip's playing position. Replies are sent to /live/clip/get/playing_position, with args: track_id, clip_id, playing_position         |
| /live/clip/stop_listen/playing_position  | track_id, clip_id                                                   |                                                                                        | Stop listening for clip's playing position.                                                                                                              |
| /live/clip/get/loop_start                | track_id, clip_id                                                   | track_id, clip_id, loop_start                                                          | Get clip's loop start                                                                                                                                    |
| /live/clip/set/loop_start                | track_id, clip_id, loop_start                                       |                                                                                        | Set clip's loop start                                                                                                                                    |
| /live/clip/get/loop_end                  | track_id, clip_id                                                   | track_id, clip_id, loop_end                                                            | Get clip's loop end                                                                                                                                      |
| /live/clip/set/loop_end                  | track_id, clip_id, loop_end                                         |                                                                                        | Set clip's loop end                                                                                                                                      |
| /live/clip/get/warping                   | track_id, clip_id                                                   | track_id, clip_id, warping                                                             | Get clip's warp mode                                                                                                                                     |
| /live/clip/set/warping                   | track_id, clip_id, warping                                          |                                                                                        | Set clip's warp mode                                                                                                                                     |
| /live/clip/get/start_marker              | track_id, clip_id                                                   | track_id, clip_id, start_marker                                                        | Get clip's start marker                                                                                                                                  |
| /live/clip/set/start_marker              | track_id, clip_id, start_marker                                     |                                                                                        | Set clip's start marker, expressed in floating-point beats                                                                                               |
| /live/clip/get/end_marker                | track_id, clip_id                                                   | track_id, clip_id, end_marker                                                          | Get clip's end marker                                                                                                                                    |
| /live/clip/set/end_marker                | track_id, clip_id, end_marker                                       |                                                                                        | Set clip's end marker, expressed in floating-point beats                                                                                                 |

</details>

---

## Device API

Represents an instrument or effect.

 - Changes for any Parameter property can be listened for by calling `/live/device/start_listen/parameter/value <track_index> <device index> <parameter_index>`

<details>
<summary><b>Documentation</b>: Device API</summary>

| Address                                  | Query params                             | Response params                          | Description                                                                             |
|:-----------------------------------------|:-----------------------------------------|:-----------------------------------------|:----------------------------------------------------------------------------------------|
| /live/device/get/name                    | track_id, device_id                      | track_id, device_id, name                | Get device name                                                                         |
| /live/device/get/class_name              | track_id, device_id                      | track_id, device_id, class_name          | Get device class_name                                                                   |
| /live/device/get/type                    | track_id, device_id                      | track_id, device_id, type                | Get device type                                                                         |
| /live/device/get/num_parameters          | track_id, device_id                      | track_id, device_id, num_parameters      | Get the number of parameters exposed by the device                                      |
| /live/device/get/parameters/name         | track_id, device_id                      | track_id, device_id, [name, ...]         | Get the list of parameter names exposed by the device                                   |
| /live/device/get/parameters/value        | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the device parameter values                                                         |
| /live/device/get/parameters/min          | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the device parameter minimum values                                                 |
| /live/device/get/parameters/max          | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the device parameter maximum values                                                 |
| /live/device/get/parameters/is_quantized | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the list of is_quantized settings (i.e., whether the parameter must be an int/bool) |
| /live/device/set/parameters/value        | track_id, device_id, value, value ...    |                                          | Set the device parameter values                                                         |
| /live/device/get/parameter/value         | track_id, device_id, parameter_id        | track_id, device_id, parameter_id, value | Get a device parameter value                                                            |
| /live/device/get/parameter/value_string  | track_id, device_id, parameter_id        | track_id, device_id, parameter_id, value | Get the device parameter value as a readable string ex: 2500 Hz                         |
| /live/device/set/parameter/value         | track_id, device_id, parameter_id, value |                                          | Set a device parameter value                                                            |

For devices:

- `name` is the human-readable name
- `type` is 1 = audio_effect, 2 = instrument, 4 = midi_effect
- `class_name` is the Live instrument/effect name, e.g. Operator, Reverb. For external plugins and racks, can be
  AuPluginDevice, PluginDevice, InstrumentGroupDevice...

</details>

 ---

# Utilities

Included with the framework is a command-line console utility `run-console.py`, which can be used as a quick and easy way to send OSC queries to AbletonOSC. Example:

```
(1653)(AbletonOSC)$ ./run-console.py
AbletonOSC command console
Usage: /live/osc/command [params]
>>> /live/song/set/tempo 123.0
>>> /live/song/get/tempo
(123.0,)
>>> /live/song/get/track_names
('1-MIDI', '2-MIDI', '3-Audio', '4-Audio')
```

# Acknowledgements

Thanks to [Stu Fisher](https://github.com/stufisher/) (and other authors) for LiveOSC, the spiritual predecessor to this
library. Thanks to [Julien Bayle](https://structure-void.com/ableton-live-midi-remote-scripts/#liveAPI)
and [NSUSpray](https://nsuspray.github.io/Live_API_Doc/) for providing XML API docs, based on original work
by [Hanz Petrov](http://remotescripts.blogspot.com/p/support-files.html).

For code contributions and feedback, many thanks to:
- Jörn Lengwenings ([Coupe70](https://github.com/Coupe70))
- Bill Moser ([billmoser](https://github.com/billmoser))
- [stevmills](https://github.com/stevmills)
- Marco Buongiorno Nardelli ([marcobn](https://github.com/marcobn)) and Colin Stokes
- Mark Marijnissen ([markmarijnissen](https://github.com/markmarijnissen))
- [capturcus](https://github.com/capturcus)

