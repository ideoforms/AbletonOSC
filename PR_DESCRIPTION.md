# Device Variations API Support for Live 12

Adds comprehensive OSC control for Device Variations (Macro Variations) in Ableton Live 12, enabling remote control of rack variation states and parameters.

## What's Added

### Core API

**Properties (Read-only):**
- `variation_count` - Number of available variations

**Properties (Read/Write):**
- `selected_variation_index` - Get/set active variation (-1 = none)

**Methods:**
- `recall_selected_variation()` - Recall the selected variation
- `recall_last_used_variation()` - Recall last used variation
- `store_variation([index])` - Store current state as variation
- `delete_selected_variation()` - Delete selected variation
- `randomize_macros()` - Randomize macro values

**Developer Tool:**
- `/live/device/introspect` - OSC endpoint to discover all properties/methods on any device

### Listeners

Standard listeners are automatically available for all properties:
- `/live/device/start_listen/variation_count`
- `/live/device/start_listen/selected_variation_index`
- (and corresponding `stop_listen` endpoints)

## Implementation Details

### Discovery Process

Used introspection to discover Live 12 API:
1. Created `/live/device/introspect` handler in `device.py`
2. Discovered `RackDevice` exposes: `variation_count`, `selected_variation_index`, and variation methods
3. Implemented only variation-specific properties (excluded general rack properties like `chains`, `macros_mapped` to keep PR focused)

### Files Changed

**Core Implementation:**
- `abletonosc/device.py` - Added variation properties, methods, and introspection handler

**Tests:**
- `tests/test_device.py` - 9 automated pytest tests with auto-skip if no RackDevice available

**Developer Tools:**
- `utils/introspect.py` - Generic introspection CLI tool for any Live object (extensible)

**Documentation:**
- Updated `.gitignore` to exclude `devel/` and `logs/`
- Development scripts moved to `devel/` (excluded from git)

## Testing

**Automated Tests (pytest):**
- ✅ Property getters (`variation_count`)
- ✅ Property get/set (`selected_variation_index`)
- ✅ All variation methods (`recall_*`, `randomize_macros`)
- ✅ Listeners (start/stop)
- ✅ Auto-skip when no suitable RackDevice found

**Manual Testing:**
- ✅ Tested with Live 12 Beta on RackDevice with 4 variations
- ✅ Variation switching (-1 → 0 → -1) confirmed working
- ✅ All read operations functional

## Usage Examples

### Via Interactive Console
```bash
./run-console.py
>>> /live/device/get/variation_count 0 0
>>> /live/device/set/selected_variation_index 0 0 1
>>> /live/device/recall_selected_variation 0 0
```

### Via Introspection Tool
```bash
./utils/introspect.py device 0 0  # Discover all properties/methods
```

### Via Python Client
```python
from client import AbletonOSCClient

client = AbletonOSCClient()
count = client.query("/live/device/get/variation_count", [0, 0])
client.send_message("/live/device/set/selected_variation_index", [0, 0, 1])
```

### Via Raw OSC
```
Send to 127.0.0.1:11000
/live/device/get/variation_count 0 0
/live/device/set/selected_variation_index 0 0 1
```

## Compatibility

**Requirements:**
- Live 12+ (variations introduced in Live 12)
- Only works with RackDevice objects (Instrument Rack, Effect Rack, Drum Rack)

**Graceful Degradation:**
- Properties return errors on non-RackDevice types
- Works alongside existing Live 11 functionality

## Future Extensions

The `/live/device/introspect` endpoint is designed to be extensible. Future PRs could add:
- `/live/clip/introspect`
- `/live/track/introspect`
- `/live/song/introspect`

The `utils/introspect.py` tool is already structured to support these once implemented.

---

**Testing:** Run `pytest tests/test_device.py` (requires Live 12 with a RackDevice containing variations)
