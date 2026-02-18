# ADDING_INFERENCE_ENGINES

## Purpose
Explain exactly how to add new inference engines in this project, with emphasis on the config schema that drives GUI controls and the adapter functions that run inference.

## Conceptual Model
Adding an inference engine is a two-part contract:

1. `Config contract` (GUI-facing):
- You declare engine parameters in `configs/tts_config.json` or `configs/s2s_config.json`.
- `src/view.py` builds widgets from that config.
- User selections are stored under speaker-level `settings` using each parameter `attribute`.

2. `Runtime contract` (inference-facing):
- `src/model.py` forwards `speaker_settings` into adapter calls.
- `src/tts_engines.py` / `src/s2s_engines.py` read those same keys and run load/generate/process functions.

If config keys and adapter lookups match, integration is modular and works without custom GUI/controller branches.

## Step-by-Step Trace (Conceptual Example)
1. Add new engine block with `parameters[]` in config.
2. View dynamically creates widgets from `parameters[]`.
3. User sets values; view stores them in `speaker["settings"][attribute]`.
4. Controller saves generation settings.
5. Model loads engine with `load_selected_*_engine(..., **speaker_settings)`.
6. Model generates through adapter using those same keys.

Pseudo snippet:
```python
# view layer (conceptual)
for param in engine_config["parameters"]:
    widget = create_widget_for_parameter(param)
    # widget value later stored under speaker settings by param["attribute"]

# model layer (conceptual)
speaker_settings = speaker["settings"]
load_selected_tts_engine(tts_engine_name, speaker_id, **speaker_settings)
audio_path = generate_audio_proxy(sentence, speaker_settings, s2s_validated)

# adapter layer (conceptual)
def load_with_mytts(**kwargs):
    model_name = kwargs.get("mytts_model")
    ...

def generate_with_mytts(tts_engine, sentence, voice_parameters, audio_path):
    speed_ui = voice_parameters.get("mytts_speed")
    speed = round(speed_ui / 100, 2)
    ...
```

## Single Parameter Journey Example (`mytts_speed`)
1. Config defines:
- `attribute: "mytts_speed"`
- `type: "slider"`
- `step: 100`
2. View stores integer UI value (example `130`) into speaker settings.
3. Model forwards that value through adapter call payload.
4. Adapter normalizes `130 / 100 -> 1.30` before inference.

## TTS and S2S Follow the Same Pattern
- Both use config-defined parameters and `attribute` keys.
- Both are loaded in model via adapter dispatch.
- Only runtime method names differ:
  - TTS: `load_*` + `generate_*`
  - S2S: `load_*` + `process_*`

## Filesystem Prerequisite (Engine/Voice Folders)
Create both folders when adding a new engine:
- `engines/<engine_key>/`
- `voices/<engine_key>/`

What they do:
- `engines/<engine_key>/`
  - Stores engine runtime artifacts (models, tokenizers, indexes, engine configs).
- `voices/<engine_key>/`
  - Stores reference voice assets used by that engine.
  - Typical structure is `voices/<engine_key>/<voice_name>/` with files such as `.wav` and optional `.txt`.

How to add them:
1. Pick an engine key (example: `mytts`).
2. Create folders:
   - `engines/mytts/`
   - `voices/mytts/`
3. Point config `folder_path` fields to those folders in `configs/tts_config.json` or `configs/s2s_config.json`.
4. Place model/runtime files under `engines/mytts/`.
5. Place voice references under `voices/mytts/<voice_name>/`.
6. Ensure adapter code reads matching attributes and paths in `src/tts_engines.py` or `src/s2s_engines.py`.

## Config Schema Reference (Exact Options From `view.py`)
This is the core reference for what can be configured.

### Engine Block Shape
For TTS (`configs/tts_config.json`):
```json
{
  "name": "EngineName",
  "upload_params": {
    "AI Models": [],
    "Voice Reference File": []
  },
  "parameters": []
}
```

For S2S (`configs/s2s_config.json`):
```json
{
  "name": "EngineName",
  "label": "Engine Settings",
  "upload_params": {
    "AI Models": [],
    "Voice Reference File": []
  },
  "parameters": []
}
```

### `parameters[]` Shared Base Keys
Each parameter entry should include:
- `label` (`str`): UI label.
- `type` (`str`): one of supported types below.
- `attribute` (`str`): canonical key used for settings + runtime lookups.

Optional cross-parameter key:
- `relies_on` (`str`): attribute name of another parameter; used to build dependent combobox path/options.

### Supported `type` Values
From `AudiobookMakerView.create_widget_for_parameter(...)`:
- `text`
- `file`
- `spinbox`
- `checkbox`
- `combobox`
- `slider`

Any other type is rejected by view as unknown.

### Type-Specific Keys
`text`:
- Required: `label`, `type`, `attribute`

`file`:
- Required: `label`, `type`, `attribute`
- Optional: `file_filter` (Qt file dialog filter string)

`spinbox`:
- Required: `label`, `type`, `attribute`
- Recommended: `min`, `max`, `default`

`checkbox`:
- Required: `label`, `type`, `attribute`

`slider`:
- Required: `label`, `type`, `attribute`, `min`, `max`
- Recommended: `default`
- Optional but commonly needed: `step`
- What `step` means in this project:
  - UI slider values are integers (PySide slider behavior).
  - `step` defines the scale factor used to convert that integer into the runtime value expected by inference code.
  - Typical runtime conversion pattern in adapter logic:
    - `runtime_value = round(ui_value / step, 2)`
- Example:
  - Config: `"attribute": "mytts_speed", "type": "slider", "min": 1, "max": 200, "step": 100`
  - User sets slider to `135` in GUI.
  - Saved value in speaker settings: `135` (integer).
  - Adapter converts to runtime speed: `round(135 / 100, 2) = 1.35`.

`combobox`:
- Required: `label`, `type`, `attribute`, `function`
- For this project, `function` is typically `get_combobox_items`
- Additional keys are interpreted by `get_combobox_items(...)`:
  - `look_for`: `folders` | `files` | `custom`
  - `folder_path`: base path for folder/file discovery
  - `file_filter`: wildcard/filter spec for files
  - `include_none_option`: `true|false`
  - `none_option_label`: label text for the none/default entry
  - `custom_options`: list used when `look_for == "custom"`
  - `relies_on`: parent attribute used to resolve dependent options

### `combobox` Lookup Behavior Details
`look_for: "folders"`:
- Lists directories under `folder_path`.

`look_for: "files"`:
- Lists files under `folder_path`.
- Applies `file_filter` when present.

`look_for: "custom"`:
- Uses `custom_options` exactly as option values.

`relies_on` behavior:
- If set, the selected value of the parent widget is appended to `folder_path`.
- Used for dependent selection patterns (for example pick voice folder first, then pick files inside it).

### Upload Config Shape (`upload_params`)
`upload_params` is used by `UploadDialog` and should contain two mode keys:
- `AI Models`
- `Voice Reference File`

Each entry supports:
- `label`
- `type` (`text` or `file`)
- `attribute`
- Optional for `file`: `file_filter`
- Optional save metadata:
  - `save_path`
  - `save_format` (`file` or `folder`)

If a `text` upload entry has no `save_path`, it is treated as a naming field (for example model/voice name).

## Minimal Compatibility Checklist
1. Config:
- Engine appears in the correct config list (`tts_engines` or `s2s_engines`).
- Parameters use supported `type`.
- Every runtime field has a stable `attribute`.
- Required filesystem paths exist for engine and voices (unless intentionally overridden):
  - `engines/<engine_key>/`
  - `voices/<engine_key>/`

2. Adapter dispatch:
- New engine branch added in dispatcher:
  - TTS: `load_tts_engine`, `generate_audio`
  - S2S: `load_s2s_engine`, `process_audio`

3. Adapter functions:
- Implement:
  - TTS: `load_with_<engine>`, `generate_with_<engine>`
  - S2S: `load_with_<engine>`, `process_with_<engine>`
- Read values using the exact config `attribute` names.

4. Runtime flow:
- No custom special-case route in controller/view.
- Engine works through normal flow:
  - `speaker_settings` -> model loader -> adapter function.

## Related Files
- `configs/tts_config.json`
- `configs/s2s_config.json`
- `src/view.py`
- `src/controller.py`
- `src/model.py`
- `src/tts_engines.py`
- `src/s2s_engines.py`
