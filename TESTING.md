# Testing Guide - Device Variations API

Complete testing checklist for the Device Variations feature.

## Prerequisites

- ✅ Ableton Live 12 (Beta or Release)
- ✅ An Instrument Rack or Effect Rack with at least 2 variations
- ✅ Python 3.x installed

## Testing Steps

### 1️⃣ **Reload AbletonOSC in Live**

**Why?** Live needs to load the modified `device.py` file.

**How:**
1. Open Ableton Live 12
2. Go to **Preferences → MIDI**
3. Under **Control Surface**, find AbletonOSC
4. Select "None" then re-select "AbletonOSC"
5. **OR** Restart Ableton Live completely

**Verify:**
- Check Live's Log.txt for "AbletonOSC: Listening on port 11000"
- Log location:
  - macOS: `~/Library/Preferences/Ableton/Live 12.x/Log.txt`
  - Windows: `%USERPROFILE%\AppData\Roaming\Ableton\Live 12.x\Log.txt`

---

### 2️⃣ **Prepare Test Set**

1. Create or open a Live set
2. Add an **Instrument Rack** (or Effect Rack) to any track
3. Create at least **2 variations**:
   - Adjust some macro knobs
   - Click the "Store Variation" button (📥 icon)
   - Repeat to create variation 2
4. Note the **track index** and **device index** (usually track 0, device 0)

---

### 3️⃣ **Quick Smoke Test - Interactive Console**

**Test basic connectivity:**

```bash
cd /Users/elzinko/Music/Ableton/User\ Library/Remote\ Scripts/AbletonOSC
./run-console.py
```

**Run these commands:**
```
>>> /live/device/get/variation_count 0 0
# Should return: (0, 0, <number_of_variations>)

>>> /live/device/get/selected_variation_index 0 0
# Should return: (0, 0, <current_variation_index>)  (-1 if none selected)

>>> /live/device/set/selected_variation_index 0 0 0
# Should switch to variation 0 (you should see it in Live)

>>> /live/device/recall_selected_variation 0 0
# Should recall the selected variation
```

**Expected Results:**
- ✅ No errors in console
- ✅ Variation changes visible in Live UI
- ✅ Values returned match what you see in Live

---

### 4️⃣ **Introspection Test**

**Verify the introspection handler works:**

```bash
./utils/introspect.py device 0 0
```

**Expected Output:**
```
INTROSPECTION: DEVICE 0 0
================================================================================

📋 PROPERTIES:
--------------------------------------------------------------------------------
🎯 HIGHLIGHTED (variation, macro, chain, selected, etc.):
  ✨ selected_variation_index=-1
  ✨ variation_count=2

📝 ALL PROPERTIES (XX total):
  • class_name=...
  • name=...
  • selected_variation_index=-1
  • type=...
  • variation_count=2
  ...

🔧 METHODS:
--------------------------------------------------------------------------------
🎯 HIGHLIGHTED (variation, macro, chain, recall, etc.):
  ✨ delete_selected_variation()
  ✨ randomize_macros()
  ✨ recall_last_used_variation()
  ✨ recall_selected_variation()
  ✨ store_variation()
  ...
```

**Expected Results:**
- ✅ `variation_count` shows correct number
- ✅ `selected_variation_index` shows -1 or 0+
- ✅ All variation methods listed

---

### 5️⃣ **Automated Tests (pytest)**

**Run the test suite:**

```bash
# Install pytest if not already installed
pip install pytest

# Run device variation tests
pytest tests/test_device.py -v
```

**Expected Output:**
```
tests/test_device.py::test_device_variation_count PASSED
tests/test_device.py::test_device_variation_count_listener PASSED
tests/test_device.py::test_device_selected_variation_index_get PASSED
tests/test_device.py::test_device_selected_variation_index_set PASSED
tests/test_device.py::test_device_selected_variation_index_listener PASSED
tests/test_device.py::test_device_recall_selected_variation PASSED
tests/test_device.py::test_device_recall_last_used_variation PASSED
tests/test_device.py::test_device_randomize_macros PASSED

======================== 8 passed in X.XXs ========================
```

**Note:** Tests will auto-skip if no RackDevice with variations is found on track 0, device 0.

**If tests are skipped:**
```
tests/test_device.py::test_device_variation_count SKIPPED
Reason: No RackDevice with variations found on track 0, device 0
```

**Solution:** Edit `tests/test_device.py` and change `RACK_TRACK_ID` and `RACK_DEVICE_ID` to match your setup.

---

### 6️⃣ **Manual Integration Test**

**Run the development test script:**

```bash
./devel/test_device_variations.py
```

**This script tests:**
- ✅ All read-only properties
- ✅ Read/write property (with restore)
- ✅ All variation methods
- ⚠️ Destructive methods (commented out by default)

**Expected Output:**
```
TEST DES APIS DE DEVICE VARIATIONS - LIVE 12
================================================================================
🎛️  Device testé:
   Name: Your Rack Name
   Class: MidiEffectGroupDevice

📖 TEST 1: Propriétés en lecture seule
--------------------------------------------------------------------------------
  ✅ variation_count: 2 (Nombre de variations)

📝 TEST 2: Propriété selected_variation_index (lecture/écriture)
--------------------------------------------------------------------------------
  📌 Variation actuelle: -1
  📊 Nombre total de variations: 2
  🔄 Changement vers variation 0...
  ✅ Variation changée avec succès vers: 0
  ↩️  Variation restaurée: -1

🔧 TEST 3: Méthodes de variations
--------------------------------------------------------------------------------
  🧪 Test: recall_selected_variation
     ✅ Rappeler la variation sélectionnée - Commande envoyée
  ...

✅ TESTS TERMINÉS
```

---

## 🐛 Troubleshooting

### Problem: "Connection error" or "No response"

**Check:**
1. Is Live running?
2. Is AbletonOSC loaded? (Check Preferences → MIDI → Control Surface)
3. Is port 11000 free? `lsof -i :11000` (should show Python process)

**Solution:**
- Restart Live
- Reload AbletonOSC (step 1️⃣)

---

### Problem: Tests fail with "No RackDevice found"

**Check:**
1. Do you have a Rack on the specified track/device?
2. Does the Rack have variations?

**Solution:**
- Create a Rack with variations on track 0
- Or edit test file to use correct track/device indices

---

### Problem: "Property not found" errors

**Check:**
- Did you reload AbletonOSC after modifying `device.py`? (step 1️⃣)

**Solution:**
- **Restart Ableton Live completely**
- Verify changes are in the correct file location

---

### Problem: Introspection shows no variation properties

**Check:**
- Is the device a RackDevice? (Not a regular plugin)
- Run: `./run-console.py` then `/live/device/get/class_name 0 0`
- Should return something with "GroupDevice" (e.g., "MidiEffectGroupDevice")

**Solution:**
- Use an Instrument Rack, Effect Rack, or Drum Rack
- Regular plugins don't support variations

---

## ✅ Success Criteria

Your implementation is working correctly if:

- ✅ Interactive console commands return expected values
- ✅ Introspection shows variation properties/methods
- ✅ Pytest tests pass (or skip gracefully)
- ✅ Variation changes in Live when using OSC commands
- ✅ No errors in Live's Log.txt

---

## 📝 Next Steps After Testing

Once all tests pass:

1. ✅ Create the Pull Request on GitHub
2. ✅ Copy `PR_DESCRIPTION.md` content to PR description
3. ✅ Link to test results in PR comments
4. ✅ Wait for maintainer review

---

## 🔗 Useful Commands Reference

```bash
# Interactive console
./run-console.py

# Introspection
./utils/introspect.py device <track_id> <device_id>

# Run tests
pytest tests/test_device.py -v

# Development test (comprehensive)
./devel/test_device_variations.py

# Check Live log
tail -f ~/Library/Preferences/Ableton/Live\ 12.*/Log.txt  # macOS
```
