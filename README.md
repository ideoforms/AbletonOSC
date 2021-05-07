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

API docs are in progress. Key calls are detailed below.

| Address | Params | Description |
|--------------------------------|
| /live/test | | Display a test message and sends an OSC reply |
| /live/application/version | | Query Live's version |
| /live/song/start_playing | | Start session playback |
| /live/song/stop_playing | | Stop session playback |
| /live/song/get/tempo | | |
| /live/song/set/tempo | tempo_bpm | |


## Acknowledgements

Thanks to [Stu Fisher](https://github.com/stufisher/) (and other authors) for LiveOSC, the spiritual predecessor to this library. Thanks to [Julien Bayle](https://structure-void.com/ableton-live-midi-remote-scripts/#liveAPI) and [NSUSpray](https://nsuspray.github.io/Live_API_Doc/) for providing XML API docs, based on original work by [Hans Petrov](http://remotescripts.blogspot.com/p/support-files.html).
