# AbletonOSC: Control Ableton Live 11+ with Open Sound Control (OSC)

AbletonOSC is a MIDI remote script that provides an OSC interface to control [Ableton Live 11+](https://www.ableton.com/en/live/). Building on ideas from the older [LiveOSC](https://github.com/hanshuebner/LiveOSC) scripts, its aim is to expose the entire [Live Object Model](https://docs.cycling74.com/max8/vignettes/live_object_model) API, enabling top-to-bottom control over Live's control interfaces.

## Installation

To install the script:

 - Clone this repo, or download/unzip and rename AbletonOSC-master to AbletonOSC
 - Move the AbletonOSC folder to the MIDI Remote Scripts folder inside the Ableton application: `/Applications/Ableton Live*.app/Contents/App-Resources/MIDI Remote Scripts`
 - Restart Live
 - In `Preferences > MIDI`, add the new AbletonOSC Control Surface that should appear. Live should display a message saying "AbletonOSC: Listening for OSC on port 11000"

## Usage

AbletonOSC listens for OSC messages on port **11000**, and sends replies on port **11001**. 

## Acknowledgements

Thanks to [Stu Fisher](https://github.com/stufisher/) (and other authors) for LiveOSC, the spiritual predecessor to this library. Thanks to [Julien Bayle](https://structure-void.com/ableton-live-midi-remote-scripts/#liveAPI) and [NSUSpray](https://nsuspray.github.io/Live_API_Doc/) for providing XML API docs, based on original work by [Hans Petrov](http://remotescripts.blogspot.com/p/support-files.html).
