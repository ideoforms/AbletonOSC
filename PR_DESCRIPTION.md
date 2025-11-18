Adds comprehensive support for Device Variations (Macro Variations) introduced in Live 12, enabling OSC control of rack variation states and parameters.

## What's Added

### New Device Properties (Read-only)
- `variation_count` - Number of available variations

### New Device Properties (Read/Write)
- `selected_variation_index` - Get/set active variation (-1 = none)

### New Device Methods
- `recall_selected_variation()` - Recall the selected variation
- `recall_last_used_variation()` - Recall last used variation
- `store_variation([index])` - Store current state as variation
- `delete_selected_variation()` - Delete selected variation
- `randomize_macros()` - Randomize macro values

### Developer Tools
- `/live/device/introspect` endpoint - Lists all available properties/methods on a device (useful for API discovery)

## Testing

All core functionality tested with Live 12 Beta:
- ✅ All read-only properties working
- ✅ `selected_variation_index` read/write tested (switching between variations)
- ✅ `recall_*` methods operational

Test scripts included:
- `introspect_device.py` - Device API discovery tool
- `test_device_variations.py` - Manual integration test script
- `tests/test_device.py` - Automated pytest unit tests (9 tests)

## Compatibility

Requires Live 12+ (variations feature introduced in Live 12). Properties will fail gracefully on non-RackDevice types or earlier Live versions.

## Documentation

Complete implementation documentation in `DEVICE_VARIATIONS_PROPOSAL.md` including:
- Full API reference with all endpoints
- Usage examples
- Test results
- Compatibility notes
