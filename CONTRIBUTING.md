# Contributing

## Tests

For unit tests to pass:

- Live must be configured with default audio input and output devices, and
- Live must be started with a blank default set

To run unit tests, `pip3 install pytest`, start Live, change to the `AbletonOSC` directory, and run:

```
pytest
```

## Live reloading

AbletonOSC supports dynamic reloading of the handler code modules so that it's not necessary to restart Live each time the code is modified.

To reload the codebase, send an OSC message to `/live/reload`. 

## Logging

Logging can be performed from any of the AbletonOSCHandler classes via the `self.logger` property.

AbletonOSC logs internal events to `logs/abletonosc.log` relative to the AbletonOSC directory.

## Debugging compile-time issues

To view the Live boot log:

```
LOG_DIR="$HOME/Library/Application Support/Ableton/Live Reports/Usage"
LOG_FILE=$(ls -atr "$LOG_DIR"/*.log | tail -1)
echo "Log path: $LOG_FILE"
tail -5000f "$LOG_FILE" | grep AbletonOSC
```
