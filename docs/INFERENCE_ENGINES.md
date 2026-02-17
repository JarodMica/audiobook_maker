# INFERENCE_ENGINES

## Purpose
Document all inference adapter functions and parameters for TTS/S2S modular runtime behavior.

## Complete Function Parameter Inventory
This inventory is generated from current source signatures and is intended to map every discovered function/method parameter.

### `s2s_engines.py` -> `dict_to_object.DictToObject`

- `__init__(self: Any, dictionary: Any) -> Any`
  - Parameters:
    - `dictionary` (`Any`): Input parameter used by this function for its operation.

- `__repr__(self: Any) -> Any`
  - Parameters: none (instance context only).

### `s2s_engines.py` -> `module`

- `process_audio(s2s_engine: Any, s2s_engine_name: Any, input_audio_path: Any, output_audio_path: Any, parameters: Any) -> Any`
  - Parameters:
    - `s2s_engine` (`Any`): Loaded S2S engine instance passed to adapter functions.
    - `s2s_engine_name` (`Any`): Selected speech-to-speech engine name.
    - `input_audio_path` (`Any`): Source path for S2S processing input audio.
    - `output_audio_path` (`Any`): Destination path for processed output audio.
    - `parameters` (`Any`): Input parameter used by this function for its operation.

- `process_with_rvc(s2s_engine: Any, input_audio_path: Any, output_audio_path: Any) -> Any`
  - Parameters:
    - `s2s_engine` (`Any`): Loaded S2S engine instance passed to adapter functions.
    - `input_audio_path` (`Any`): Source path for S2S processing input audio.
    - `output_audio_path` (`Any`): Destination path for processed output audio.

- `load_s2s_engine(s2s_engine_name: Any, **kwargs: Any) -> Any`
  - Parameters:
    - `s2s_engine_name` (`Any`): Selected speech-to-speech engine name.
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_with_rvc(**kwargs: Any) -> Any`
  - Parameters:
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_config(config_path: Any) -> Any`
  - Parameters:
    - `config_path` (`Any`): Path to a JSON/YAML configuration file.

- `dict_to_object(src: Any) -> Any`
  - Parameters:
    - `src` (`Any`): Input parameter used by this function for its operation.

### `tts_engines.py` -> `dict_to_object.DictToObject`

- `__init__(self: Any, dictionary: Any) -> Any`
  - Parameters:
    - `dictionary` (`Any`): Input parameter used by this function for its operation.

- `__repr__(self: Any) -> Any`
  - Parameters: none (instance context only).

### `tts_engines.py` -> `module`

- `generate_audio(tts_engine: Any, sentence: Any, voice_parameters: Any, tts_engine_name: Any, audio_path: Any) -> Any`
  - Parameters:
    - `tts_engine` (`Any`): Loaded TTS engine instance passed to adapter functions.
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `tts_engine_name` (`Any`): Selected text-to-speech engine name.
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `generate_with_pyttsx3(tts_engine: Any, sentence: Any, voice_parameters: Any, audio_path: Any) -> Any`
  - Parameters:
    - `tts_engine` (`Any`): Loaded TTS engine instance passed to adapter functions.
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `generate_with_styletts2(tts_engine: Any, sentence: Any, voice_parameters: Any, audio_path: Any) -> Any`
  - Parameters:
    - `tts_engine` (`Any`): Loaded TTS engine instance passed to adapter functions.
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `generate_with_tortoise(tts_engine: Any, sentence: Any, voice_parameters: Any, audio_path: Any) -> Any`
  - Parameters:
    - `tts_engine` (`Any`): Loaded TTS engine instance passed to adapter functions.
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `generate_with_xtts(tts_engine: Any, sentence: Any, voice_parameters: Any, audio_path: Any) -> Any`
  - Parameters:
    - `tts_engine` (`Any`): Loaded TTS engine instance passed to adapter functions.
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `generate_with_f5tts(tts_engine: Any, sentence: Any, voice_parameters: Any, audio_path: Any) -> Any`
  - Parameters:
    - `tts_engine` (`Any`): Loaded TTS engine instance passed to adapter functions.
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `generate_with_gpt_sovits(tts_engine: Any, sentence: Any, voice_parameters: Any, audio_path: Any) -> Any`
  - Parameters:
    - `tts_engine` (`Any`): Loaded TTS engine instance passed to adapter functions.
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `load_tts_engine(tts_engine_name: Any, **kwargs: Any) -> Any`
  - Parameters:
    - `tts_engine_name` (`Any`): Selected text-to-speech engine name.
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_with_styletts2(**kwargs: Any) -> Any`
  - Parameters:
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_with_tortoise(**kwargs: Any) -> Any`
  - Parameters:
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_with_xtts(**kwargs: Any) -> Any`
  - Parameters:
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_with_f5tts(**kwargs: Any) -> Any`
  - Parameters:
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_with_gpt_sovits(**kwargs: Any) -> Any`
  - Parameters:
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `find_engine_config(engine_name: Any, tts_settings: Any) -> Any`
  - Parameters:
    - `engine_name` (`Any`): Selected inference engine name from combobox.
    - `tts_settings` (`Any`): Parsed TTS configuration object used for engine lookups.

- `load_tts_config(path: Any = 'configs/tts_config.json') -> Any`
  - Parameters:
    - `path` (`Any`): Input parameter used by this function for its operation. Default: `'configs/tts_config.json'`.

- `load_config(config_path: Any) -> Any`
  - Parameters:
    - `config_path` (`Any`): Path to a JSON/YAML configuration file.

- `dict_to_object(src: Any) -> Any`
  - Parameters:
    - `src` (`Any`): Input parameter used by this function for its operation.

## Related Files
- `src/model.py`
- `src/view.py`
- `src/controller.py`
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `configs/tts_config.json`
- `configs/s2s_config.json`
