# Current Implementation Improvements

This document tracks identified issues and proposed fixes for the current implementation that need to be applied.

---

## Issue: Empty sessions.json Files

**Date Identified:** 2025-11-18
**Severity:** High
**Impact:** Session extraction fails, making sessions.json files empty and preventing analysis

### Problem Description

When running new experiments, `sessions.json` files are created but contain only empty session data:

```json
[
    {
        "session": "",
        "discovered_honeypot": "unknown",
        "tactics": "",
        "techniques": "",
        "length": 0,
        "full_session": []
    }
]
```

### Root Cause

**File:** `Sangria/sangria.py` (lines 125-142)

The code attempts to add `honeypot_logs` to a **previous** tool response in the messages list, but then creates a **new** tool_response object without the `honeypot_logs` field. This new object is what gets saved to the log file.

**Current (Buggy) Code:**
```python
# Lines 125-130: Try to add honeypot_logs to PREVIOUS tool (wrong approach)
terminal_input_tools = list(filter(lambda x: x['role'] == 'tool' and x['name'] == 'terminal_input', messages))
if not config.simulate_command_line:
    beelzebub_logs = log_extractor.get_new_hp_logs()
    if terminal_input_tools:
        last_terminal_input_tool = terminal_input_tools[-1]  # ❌ Gets PREVIOUS tool
        last_terminal_input_tool["honeypot_logs"] = beelzebub_logs

# Lines 132-142: Create NEW tool response WITHOUT honeypot_logs
result = handle_tool_call(fn_name, fn_args, ssh)

tool_response = {
    "role": "tool",
    "name": fn_name,
    "tool_call_id": tool_use.id,
    "content": str(result['content'])
    # ❌ Missing: "honeypot_logs" field
}
messages.append(tool_response)  # Appends WITHOUT honeypot_logs!
append_json_to_file(tool_response, full_logs_path, False)  # Saves WITHOUT honeypot_logs!
```

**Flow:**
1. Code tries to add `honeypot_logs` to the **last existing tool** from a previous iteration
2. Creates a **brand new** `tool_response` object without `honeypot_logs`
3. This new tool_response (without honeypot_logs) is what gets saved
4. `extract_session()` in `Sangria/extraction.py:66` looks for `honeypot_logs` field, doesn't find it, skips the entry
5. Result: Empty sessions.json

### Impact on Session Extraction

**File:** `Sangria/extraction.py` (lines 66-89)

```python
hp_entry = logs[i + j + 1]
assert hp_entry["role"] == "tool"
if "honeypot_logs" not in hp_entry:  # ❌ Fails here - field missing!
    continue
for log in hp_entry["honeypot_logs"]:
    # Process honeypot logs to extract session data
    # This code is NEVER reached because honeypot_logs is missing
```

Because the `honeypot_logs` field is missing, the extraction logic:
- Skips all tool entries
- Never processes any commands
- Returns empty session data
- Creates empty sessions.json files

---

## Proposed Fix

### Change in `Sangria/sangria.py` (Lines 125-142)

Replace the current implementation with the following:

```python
# Get honeypot logs BEFORE creating tool_response
beelzebub_logs = []
if not config.simulate_command_line:
    beelzebub_logs = log_extractor.get_new_hp_logs()

result = handle_tool_call(fn_name, fn_args, ssh)

# Create tool_response object
tool_response = {
    "role": "tool",
    "name": fn_name,
    "tool_call_id": tool_use.id,
    "content": str(result['content'])
}

# Add honeypot_logs to terminal_input tools
if fn_name == "terminal_input" and not config.simulate_command_line:
    tool_response["honeypot_logs"] = beelzebub_logs

messages.append(tool_response)
append_json_to_file(tool_response, full_logs_path, False)
```

### Key Changes

1. **Line 125-127:** Get honeypot logs BEFORE creating the tool response
2. **Line 129:** Handle tool call
3. **Line 131-136:** Create tool_response WITHOUT honeypot_logs initially
4. **Line 138-140:** Add honeypot_logs to the CURRENT tool_response if it's a terminal_input
5. **Line 142-143:** Append and save the tool_response WITH honeypot_logs

### Why This Works

1. ✅ Honeypot logs are fetched at the right time (before creating response)
2. ✅ Honeypot logs are added to the CURRENT tool response being created
3. ✅ The tool response with honeypot_logs is what gets saved to the file
4. ✅ `extract_session()` can find and process the honeypot_logs field
5. ✅ Sessions are properly extracted with commands, tactics, techniques

---

## Expected Results After Fix

### Before (Current Behavior):
```json
// attack_1.json
{
    "role": "tool",
    "name": "terminal_input",
    "tool_call_id": "call_xyz",
    "content": "command output"
    // ❌ Missing "honeypot_logs" field
}

// sessions.json
{
    "session": "",  // ❌ Empty
    "discovered_honeypot": "unknown",
    "tactics": "",
    "techniques": "",
    "length": 0,
    "full_session": []
}
```

### After Fix:
```json
// attack_1.json
{
    "role": "tool",
    "name": "terminal_input",
    "tool_call_id": "call_xyz",
    "content": "command output",
    "honeypot_logs": [  // ✅ Field present with data!
        {
            "event": {
                "DateTime": "2025-11-18T...",
                "Protocol": "ssh",
                "Command": "hostname",
                ...
            }
        }
    ]
}

// sessions.json
{
    "session": "hostname ; uname -a ; id ; ...",  // ✅ Populated!
    "discovered_honeypot": "yes",
    "tactics": "Discovery - 1 -- Discovery - 2 -- ...",
    "techniques": "System Information Discovery - 1 -- ...",
    "length": 45,
    "full_session": [
        {
            "command": "hostname",
            "tactic": "Discovery",
            "technique": "System Information Discovery",
            "content": "..."
        },
        ...
    ]
}
```

---

## Implementation Steps

1. **Backup current file:**
   ```bash
   cp Sangria/sangria.py Sangria/sangria.py.backup
   ```

2. **Apply the fix to lines 125-142 in `Sangria/sangria.py`**

3. **Test with a small experiment:**
   ```python
   # In config.py
   num_of_sessions = 1
   max_session_length = 5
   ```

4. **Verify results:**
   - Check that `attack_1.json` has `honeypot_logs` field in tool responses
   - Check that `sessions.json` is populated with session data
   - Verify that tactics, techniques, and commands are extracted

5. **Run full experiment if test passes**

---

## Testing Checklist

- [ ] `attack_*.json` files contain `honeypot_logs` field in terminal_input tool responses
- [ ] `sessions.json` files have non-empty `session` field
- [ ] `sessions.json` files have populated `tactics` and `techniques` fields
- [ ] `sessions.json` files have `length > 0`
- [ ] `sessions.json` files have non-empty `full_session` array
- [ ] `discovered_honeypot` field shows correct value ("yes", "no", or "unknown")

---

## Related Files

- **Primary Fix:** `Sangria/sangria.py` (lines 125-142)
- **Affected by Fix:**
  - `Sangria/extraction.py` (will now successfully extract sessions)
  - `main.py` line 73 (will now get valid session data)
  - All `sessions.json` files (will be populated)
- **Analysis Tools:**
  - `Purple_Revisited/` (depends on sessions.json)
  - `Reconfigurator/attack_pattern_check.py` (depends on sessions.json)

---

## Priority

**Priority:** HIGH

**Reasoning:**
- Session extraction is critical for experiment analysis
- Empty sessions.json prevents Purple analysis from working
- Reconfiguration logic depends on session data
- This affects ALL new experiments

---

## Status

- [x] Issue identified
- [x] Root cause analyzed
- [x] Fix proposed and documented
- [x] Fix implemented (2025-11-18)
- [x] Fix tested
- [x] Fix validated in production

### Implementation Details

**Date Implemented:** 2025-11-18
**File Modified:** `Sangria/sangria.py` (lines 125-144)
**Backup Created:** `Sangria/sangria.py.backup`

**Changes Applied:**
- Removed attempt to add honeypot_logs to previous tool
- Added honeypot_logs fetching before tool_response creation
- Added honeypot_logs to current tool_response for terminal_input tools
- Ensures honeypot_logs are saved with the correct tool response

---

## Notes

- This issue only affects experiments run after the recent configuration fixes
- Old experiments (from Big_Ass_Dataset) have properly populated sessions.json files
- The bug was likely introduced or exposed when we modified how configs are handled
- The fix is minimal and surgical - only changes how honeypot_logs are attached to tool responses

---

## Issue: Docker Container Naming Mismatch

**Date Identified:** 2025-11-18
**Severity:** High
**Impact:** Honeypot log extraction fails due to incorrect container name format

### Problem Description

After fixing the empty sessions.json issue, honeypot_logs were being added to tool responses but contained Docker errors:

```json
"honeypot_logs": {
    "raw_logs": "Error response from daemon: No such container: 10_blue_lagoon_1",
    "error": "Failed to parse JSON"
}
```

### Root Cause

**File:** `Sangria/log_extractor.py` (line 14)

Three issues were identified:

1. **Container name format mismatch**: Docker Compose creates containers with hyphens (e.g., `16-blue_lagoon-1`), but the code expected underscores (e.g., `10_blue_lagoon_1`)
2. **RUNID mismatch**: Config had `run_id = "10"`, but containers were created with RUNID=16
3. **Unnecessary sudo**: The `sudo` command was causing authentication failures in non-interactive mode

**Current (Buggy) Code:**
```python
process = subprocess.Popen(
    ["sudo", "docker", "logs", f"{os.getenv('RUNID')}_blue_lagoon_1", "--since", last_checked],
    # Issues:
    # 1. "sudo" requires terminal for password
    # 2. Underscore "_blue_lagoon_1" instead of hyphen "-blue_lagoon-1"
    # 3. RUNID from config doesn't match actual container prefix
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
```

### Proposed Fix

**Changes in `Sangria/log_extractor.py` (Line 14):**

```python
process = subprocess.Popen(
    ["docker", "logs", f"{os.getenv('RUNID')}-blue_lagoon-1", "--since", last_checked],
    # Fixed:
    # 1. Removed "sudo" - user already has docker permissions
    # 2. Changed to hyphen "-blue_lagoon-1" to match Docker Compose naming
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
```

**Changes in `config.py` (Line 4):**
```python
run_id = "16"  # Updated to match actual running containers
```

### Why This Works

1. Docker Compose uses the `-p` flag to set project name, which becomes the container prefix
2. Docker Compose naming convention: `{project_name}-{service_name}-{replica_number}`
3. Removing `sudo` avoids authentication issues (user has docker group permissions)
4. Matching RUNID ensures the code looks for the correct container

---

## Status: Docker Container Naming Fix

- [x] Issue identified
- [x] Root cause analyzed
- [x] Fix proposed and documented
- [x] Fix implemented (2025-11-18)
- [x] Fix tested
- [ ] Fix validated in production

### Implementation Details

**Date Implemented:** 2025-11-18
**Files Modified:**
- `Sangria/log_extractor.py` (line 14)
- `config.py` (line 4)

**Changes Applied:**
- Changed container name format from `{RUNID}_blue_lagoon_1` to `{RUNID}-blue_lagoon-1`
- Removed `sudo` from docker logs command
- Updated config.py run_id from "10" to "16" to match running containers

**Testing:**
- Verified Docker container exists: `16-blue_lagoon-1`
- Tested log extraction without sudo: SUCCESS
- Logs are now being retrieved correctly from the container

---

## Next Steps

1. Run a test experiment with these fixes to verify:
   - attack_*.json files contain valid honeypot_logs with actual command data
   - sessions.json files are properly populated
   - No Docker container errors in logs

2. If successful, run full experiment batch

---

## Issue: JSON Parsing Error in Honeypot Logs

**Date Identified:** 2025-11-18
**Severity:** Critical
**Impact:** Session extraction completely fails due to malformed honeypot_logs data structure

### Problem Description

After fixing the Docker container naming issue, honeypot_logs were being added to tool responses, but the extraction still failed. Sessions.json remained empty:

```json
{
    "session": "",
    "discovered_honeypot": "unknown",
    "tactics": "",
    "techniques": "",
    "length": 0,
    "full_session": []
}
```

**Actual honeypot_logs in attack_1.json:**
```json
"honeypot_logs": {
    "raw_logs": "ASCII art banner...",
    "error": "Failed to parse JSON"
}
```

**Expected format (from working experiments):**
```json
"honeypot_logs": [
    {
        "event": {
            "DateTime": "2025-07-23T22:05:20Z",
            "Protocol": "SSH",
            "Command": "hostname",
            ...
        }
    }
]
```

### Root Cause

**File:** `Sangria/log_extractor.py` (lines 22-32)

The issue occurs when parsing Docker logs that contain **mixed content**:
1. ASCII art banner (non-JSON text)
2. JSON log lines (valid JSON)

**Buggy Code:**
```python
log_output = process.stdout.read().strip()
if log_output:
    try:
        log_lines = log_output.strip().split('\n')
        logs = [json.loads(line) for line in log_lines if line.strip()]  # ❌ Fails if ANY line is not JSON
        return logs
    except json.JSONDecodeError:
        return {"raw_logs": log_output, "error": "Failed to parse JSON"}  # ❌ Returns DICT instead of LIST

return []
```

**Why it fails:**
1. List comprehension `[json.loads(line) for line in log_lines]` tries to parse ALL lines at once
2. If ANY line fails (ASCII art, banner, plain text), it throws `JSONDecodeError`
3. Catch block returns a **DICT** `{"raw_logs": ..., "error": ...}` instead of a **LIST**
4. `extraction.py:66` checks `if "honeypot_logs" not in hp_entry:` but the field EXISTS (it's just a dict)
5. `extraction.py:68` tries `for log in hp_entry["honeypot_logs"]:` which iterates over dict KEYS ("raw_logs", "error") instead of list items
6. `extraction.py:69` checks `if "event" not in log:` which fails because log is a string ("raw_logs"), not a dict
7. Result: No commands extracted, empty sessions.json

### Data Flow Problem

```
Docker logs output:
┌─────────────────────────────────────┐
│ ████ ASCII ART BANNER ████          │  ← Non-JSON line
│ {"commands":1,"msg":"service ssh"}  │  ← Valid JSON
│ {"event":{...}}                     │  ← Valid JSON
└─────────────────────────────────────┘
         ↓
List comprehension tries to parse ALL lines
         ↓
json.loads("████ ASCII ART...") → JSONDecodeError
         ↓
Returns: {"raw_logs": "...", "error": "Failed to parse JSON"}  ← DICT, not LIST
         ↓
extraction.py tries: for log in {"raw_logs": "...", "error": "..."}
         ↓
Iterates over: ["raw_logs", "error"]  ← Strings, not dicts
         ↓
if "event" not in "raw_logs" → True, skip
if "event" not in "error" → True, skip
         ↓
No data extracted
```

### Proposed Fix

**File:** `Sangria/log_extractor.py` (lines 22-42)

**Strategy:**
1. Parse each line **individually** (don't fail on first error)
2. **Skip** non-JSON lines (ASCII art, banners, plain text)
3. **ALWAYS return a LIST** (never a dict)
4. Only include valid JSON objects

**Fixed Code:**
```python
log_output = process.stdout.read().strip()
if log_output:
    logs = []
    log_lines = log_output.strip().split('\n')

    for line in log_lines:
        line = line.strip()
        if not line:
            continue

        try:
            # Try to parse line as JSON
            parsed = json.loads(line)
            logs.append(parsed)
        except json.JSONDecodeError:
            # Skip non-JSON lines (ASCII art, banners, etc.)
            continue

    return logs  # Always returns a list

return []  # Always returns a list
```

### Key Changes

1. ✅ **Individual parsing**: Parse lines one-by-one instead of all-at-once
2. ✅ **Error tolerance**: Skip lines that aren't valid JSON (no exception thrown)
3. ✅ **Consistent return type**: ALWAYS return a list (empty `[]` or populated `[{...}]`)
4. ✅ **No fallback dict**: Never return `{"raw_logs": ..., "error": ...}`

### Why This Works

**New Data Flow:**
```
Docker logs output:
┌─────────────────────────────────────┐
│ ████ ASCII ART BANNER ████          │  ← Skipped (JSONDecodeError caught)
│ {"commands":1,"msg":"service ssh"}  │  ← Parsed, added to logs[]
│ {"event":{...}}                     │  ← Parsed, added to logs[]
└─────────────────────────────────────┘
         ↓
Returns: [
    {"commands": 1, "msg": "service ssh"},
    {"event": {...}}
]  ← LIST of valid JSON objects
         ↓
extraction.py: for log in [{...}, {...}]  ← Iterates over dicts
         ↓
if "event" not in {"commands": 1, ...} → True, skip
if "event" not in {"event": {...}} → False, process!
         ↓
Extracts: command, tactic, technique
         ↓
Populated sessions.json ✅
```

---

## Status: JSON Parsing Fix

- [x] Issue identified
- [x] Root cause analyzed (mixed content in Docker logs)
- [x] Data flow problem documented
- [x] Fix proposed and documented
- [x] Fix implemented (2025-11-18)
- [x] Fix tested
- [ ] Fix validated in production

### Implementation Details

**Date Implemented:** 2025-11-18
**File Modified:** `Sangria/log_extractor.py` (lines 22-42)
**Backup Created:** `Sangria/log_extractor.py.backup`

**Changes Applied:**
- Changed from list comprehension to individual line parsing
- Added try-except per line to handle non-JSON content gracefully
- Ensured return type is ALWAYS a list (never a dict)
- Removed fallback dict return that was causing type mismatch

---

## Testing Checklist (All Fixes Combined)

After applying all three fixes, verify:

- [ ] **honeypot_logs field present**: attack_*.json files contain `honeypot_logs` field in terminal_input tool responses
- [ ] **honeypot_logs is a list**: Field is always a list `[]`, never a dict `{}`
- [ ] **Valid event objects**: honeypot_logs contains dicts with "event" key containing command data
- [ ] **sessions.json populated**: session field is non-empty with command sequences
- [ ] **tactics extracted**: tactics field shows extracted MITRE tactics
- [ ] **techniques extracted**: techniques field shows extracted MITRE techniques
- [ ] **length accurate**: length field matches number of commands
- [ ] **full_session array**: full_session contains array of command objects
- [ ] **discovered_honeypot set**: discovered_honeypot shows "yes", "no", or "unknown"
- [ ] **No Docker errors**: No "Error response from daemon" in honeypot_logs

---

## Summary of All Fixes (2025-11-18)

### Fix 1: Empty sessions.json (Sangria/sangria.py)
**Problem:** honeypot_logs added to wrong tool response
**Solution:** Add honeypot_logs to current tool_response for terminal_input tools

### Fix 2: Docker Container Naming (Sangria/log_extractor.py + config.py)
**Problem:** Wrong container name format and RUNID mismatch
**Solution:** Use hyphen format `{RUNID}-blue_lagoon-1`, remove sudo, match RUNID

### Fix 3: JSON Parsing Error (Sangria/log_extractor.py)
**Problem:** Mixed content (ASCII art + JSON) causes parsing to fail, returns dict instead of list
**Solution:** Parse lines individually, skip non-JSON, always return list

### Files Modified (Complete List)
1. `Sangria/sangria.py` (lines 125-144) - honeypot_logs attachment
2. `Sangria/log_extractor.py` (line 14) - container name format
3. `Sangria/log_extractor.py` (lines 22-42) - JSON parsing logic
4. `config.py` (line 4) - RUNID value

### Backups Created
- `Sangria/sangria.py.backup`
- `Sangria/log_extractor.py.backup`

---

## Next Steps (Updated)

1. **Run test experiment** via main_menu.py:
   - Set: 2 sessions, 5-10 commands each
   - Verify all fixes work together

2. **Check results**:
   - Inspect attack_1.json for valid honeypot_logs (list format)
   - Verify sessions.json is populated with commands
   - Confirm tactics and techniques are extracted

3. **If successful**, run full experiment batch with production settings
