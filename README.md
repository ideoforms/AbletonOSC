# AbletonOSC: Control Ableton Live 11+ with OSC

AbletonOSC is a MIDI remote script that provides an Open Sound Control (OSC) interface to control [Ableton Live 11+](https://www.ableton.com/en/live/). Building on ideas from the older [LiveOSC](https://github.com/hanshuebner/LiveOSC) scripts, its aim is to expose the entire [Live Object Model](https://docs.cycling74.com/max8/vignettes/live_object_model) API, providing comprehensive control over Live's control interfaces.

## Installation

To install the script:

 - Clone this repo, or download/unzip and rename AbletonOSC-master to AbletonOSC
 - Move the AbletonOSC folder to the MIDI Remote Scripts folder inside the Ableton application: `/Applications/Ableton Live*.app/Contents/App-Resources/MIDI Remote Scripts`
 - Restart Live
 - In `Preferences > MIDI`, add the new AbletonOSC Control Surface that should appear. Live should display a message saying "AbletonOSC: Listening for OSC on port 11000"

## Usage

AbletonOSC listens for OSC messages on port **11000**, and sends replies on port **11001**. 

### Application API

| Address | Query params | Response params | Description |
| :------ | :----------- | :-------------- | :---------- |
| /live/test | | | Display a test message and sends an OSC reply |
| /live/application/get/version | | major_version, minor_version | Query Live's version |

### Song API

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
| /live/song/get/is_playing | | tempo_bpm | Query whether the song is currently playing |
| /live/song/get/tempo | | tempo_bpm | Query song tempo |
| /live/song/set/tempo | tempo_bpm | | Set song tempo |
| /live/song/get/metronome | | metronome_on | Query metronome on/off |
| /live/song/set/metronome  | metronome_on | | Set metronome on/off |

Additional properties are exposed to `get`, `set`, `start_listen` and `stop_listen` in the same manner: `arrangement_overdub`, `back_to_arranger`, `clip_trigger_quantization`, `current_song_time`, `groove_amount`, `loop`, `loop_length`, `loop_start`,  `midi_recording_quantization`, `nudge_down`, `nudge_up`, `punch_in`, `punch_out`, `record_mode`

## Acknowledgements

Thanks to [Stu Fisher](https://github.com/stufisher/) (and other authors) for LiveOSC, the spiritual predecessor to this library. Thanks to [Julien Bayle](https://structure-void.com/ableton-live-midi-remote-scripts/#liveAPI) and [NSUSpray](https://nsuspray.github.io/Live_API_Doc/) for providing XML API docs, based on original work by [Hans Petrov](http://remotescripts.blogspot.com/p/support-files.html).
