# Proposal: Device Variations API Support for AbletonOSC

## Context

**Device Variations** (also known as Macro Variations) were introduced in Ableton Live 12 and allow saving and recalling different parameter configurations for Instrument Racks and Effect Racks.

This proposal aims to add support for variations in the AbletonOSC API.

## Research Status

### 🔍 Live 12 API Documentation

After researching the Live Object Model (LOM) documentation for Live 12:
- ✅ Live 12 is already supported by AbletonOSC (automatically detected)
- ✅ Variations APIs were discovered through introspection
- ✅ Variations are exposed via `RackDevice` object properties

### ✅ Introspection Results (2025-01-18)

An introspection handler was added to `device.py` and the following properties/methods were discovered:

#### Available Properties:
- ✅ `selected_variation_index`: Index of the active variation (-1 = none)
- ✅ `variation_count`: Number of available variations
- ✅ `can_have_chains`: Whether the device can have chains (racks)
- ✅ `chains`: List of chains in the rack
- ✅ `has_macro_mappings`: Whether the rack has macro mappings
- ✅ `macros_mapped`: Tuple indicating which macros are mapped
- ✅ `visible_macro_count`: Number of visible macros

#### Available Methods:
- ✅ `recall_selected_variation()`: Recall the selected variation
- ✅ `recall_last_used_variation()`: Recall the last used variation
- ✅ `store_variation()`: Store current configuration as a variation
- ✅ `delete_selected_variation()`: Delete the selected variation
- ✅ `randomize_macros()`: Randomize macro values

#### Available Listeners:
- ✅ `add_variation_count_listener()`: Listen to changes in variation count
- ✅ Plus all standard listeners for the properties above

### 📋 Implemented OSC API ✅

The following endpoints have been implemented in `device.py`:

#### Read-only Properties (Getters)

| Endpoint | Params | Response | Description |
|----------|--------|----------|-------------|
| `/live/device/get/variation_count` | track_id, device_id | track_id, device_id, count | Number of available variations |
| `/live/device/get/can_have_chains` | track_id, device_id | track_id, device_id, bool | Whether device can have chains |
| `/live/device/get/has_macro_mappings` | track_id, device_id | track_id, device_id, bool | Whether rack has macro mappings |
| `/live/device/get/macros_mapped` | track_id, device_id | track_id, device_id, tuple | Tuple of mapped macros |
| `/live/device/get/visible_macro_count` | track_id, device_id | track_id, device_id, count | Number of visible macros |

#### Read/Write Properties (Getters & Setters)

| Endpoint | Params | Response/Action | Description |
|----------|--------|-----------------|-------------|
| `/live/device/get/selected_variation_index` | track_id, device_id | track_id, device_id, index | Index of active variation (-1 = none) |
| `/live/device/set/selected_variation_index` | track_id, device_id, index | - | Select a variation by index |

#### Methods

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/live/device/recall_selected_variation` | track_id, device_id | Recall the selected variation |
| `/live/device/recall_last_used_variation` | track_id, device_id | Recall the last used variation |
| `/live/device/store_variation` | track_id, device_id, [index] | Store current configuration (optional index) |
| `/live/device/delete_selected_variation` | track_id, device_id | Delete the selected variation |
| `/live/device/randomize_macros` | track_id, device_id | Randomize macro values |

#### Listeners

Standard listeners are automatically available for all properties:

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/live/device/start_listen/selected_variation_index` | track_id, device_id | Listen to variation changes |
| `/live/device/stop_listen/selected_variation_index` | track_id, device_id | Stop listening |
| `/live/device/start_listen/variation_count` | track_id, device_id | Listen to variation count changes |
| `/live/device/stop_listen/variation_count` | track_id, device_id | Stop listening |

#### Introspection (Development Helper)

| Endpoint | Params | Response | Description |
|----------|--------|----------|-------------|
| `/live/device/introspect` | track_id, device_id | track_id, device_id, properties..., methods... | Lists all available properties and methods |

## Implementation Plan

### Phase 1: Exploration and Discovery ✅ COMPLETED

- [x] Create `feature/device-variations` branch
- [x] Create exploration script `explore_device_variations.py`
- [x] Create introspection handler in `device.py`
- [x] Create `introspect_device.py` script
- [x] Run script with Live 12 open
- [x] Identify all available properties and methods

### Phase 2: Implementation ✅ COMPLETED

1. **✅ Modify `abletonosc/device.py`**:
   - [x] Add properties to `properties_r`:
     - `variation_count`, `can_have_chains`, `chains`, `has_macro_mappings`,
     - `macros_mapped`, `visible_macro_count`
   - [x] Add properties to `properties_rw`:
     - `selected_variation_index`
   - [x] Add methods:
     - `recall_selected_variation`, `recall_last_used_variation`,
     - `delete_selected_variation`, `randomize_macros`
   - [x] Implement custom callback for `store_variation()`
   - [x] Implement introspection handler `/live/device/introspect`

2. **🧪 Create test script `test_device_variations.py`**:
   - [x] Tests for all read-only properties
   - [x] Tests for `selected_variation_index` (read/write)
   - [x] Tests for `recall_*` methods
   - [ ] Tests for modification methods (user validation required)

3. **📝 Documentation**:
   - [x] Update `DEVICE_VARIATIONS_PROPOSAL.md` with discovered APIs
   - [ ] Document in `README.md` (to be done before PR)

### Phase 3: Testing and Validation ✅ COMPLETED

- [x] Live 12 test set with Rack "elzinko-arp-v1" (4 variations)
- [x] Restart Live and run `./test_device_variations.py`
- [x] Validate all use cases
  - ✅ Read-only properties: `variation_count`, `can_have_chains`, etc.
  - ✅ Read/write property: `selected_variation_index` (tested -1 → 0 → -1)
  - ✅ Methods: `recall_selected_variation`, `recall_last_used_variation`
  - ⚠️ Modification methods available but not tested (for safety)
- [ ] Create unit tests in `tests/test_device.py` (optional for future PR)

### Phase 4: Pull Request 📤 PENDING

- [ ] Document API in `README.md`
- [x] Commit with descriptive message
- [ ] Create PR to `master` with:
  - Description of changes
  - Usage examples
  - Compatibility notes (Live 12+ only)
  - Test results

## Compatibility Notes

⚠️ **Important**: Device Variations are a Live 12+ feature

Options for handling compatibility:
1. **Automatic detection**: Endpoints will return `None` or error when used with Live 11
2. **Clear documentation**: Indicate in README that these endpoints require Live 12+
3. **Conditional tests**: Skip tests if Live version < 12

## User Instructions

### 🚀 How to Test Now

1. **Prepare your Live 12 set**:
   ```
   - Open Ableton Live 12
   - Create a new set or open an existing one
   - Add an Instrument Rack or Effect Rack to the first track
   - Create 2-3 macro variations with different names
   - Ensure AbletonOSC is loaded (you should see "Listening on port 11000")
   ```

2. **Run the exploration script**:
   ```bash
   cd /path/to/AbletonOSC
   python3 explore_device_variations.py
   ```

3. **Analyze the results**:
   - Properties marked ✅ are available in the API
   - Communicate results to finalize implementation

4. **Manual alternative** (via console):
   ```bash
   ./run-console.py
   >>> /live/device/get/selected_variation_index 0 0
   # If this returns a value, the API is available!
   ```

## Resources

- [Live Object Model Documentation](https://docs.cycling74.com/max8/vignettes/live_object_model)
- [AbletonOSC Device API](https://github.com/ideoforms/AbletonOSC#device-api)
- [Live 12 Macro Variations Manual](https://www.ableton.com/en/manual/working-with-instruments-and-effects/)

## Author

- Feature proposed by: @elzinko
- Date: 2025-01-18
