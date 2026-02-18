# INFERENCE_ENGINES

## Purpose
Reference for all currently wired inference engines in audiobook maker, including engine key names, parameter mapping, and runtime call flow.

## Runtime Routing
- TTS load entrypoint: `src/tts_engines.py` -> `load_tts_engine(tts_engine_name, **kwargs)`
- TTS generate entrypoint: `src/tts_engines.py` -> `generate_audio(tts_engine, sentence, voice_parameters, tts_engine_name, audio_path)`
- S2S load entrypoint: `src/s2s_engines.py` -> `load_s2s_engine(s2s_engine_name, **kwargs)`
- S2S process entrypoint: `src/s2s_engines.py` -> `process_audio(s2s_engine, s2s_engine_name, input_audio_path, output_audio_path, parameters)`

## TTS Engines

### Tortoise (`tortoise`)
- Purpose: Autoregressive + diffusion TTS with selectable model/tokenizer/voice.
- Config source: `configs/tts_config.json` (`name: "Tortoise"`).
- Required settings:
  - `voice`
- Common optional settings:
  - `autoregressive_model_path`
  - `diffusion_model_path`
  - `vocoder_name`
  - `tokenizer_json_path`
  - `tortoise_seed`
  - `sample_size`
  - `tortoise_iterations`
  - `use_deepspeed`
  - `use_hifigan`
- Load path:
  - `load_tts_engine("tortoise")` -> `load_with_tortoise(...)` -> `tortoise_tts_api.inference.load.load_tts(...)`
- Generate path:
  - `generate_audio(..., "tortoise")` -> `generate_with_tortoise(...)` -> `tortoise_tts_api.inference.generate.generate(...)`

### pyttsx3 (`pyttsx3`)
- Purpose: Local system-voice fallback engine with no model loading step.
- Config source: `configs/tts_config.json` (`name: "pyttsx3"`).
- Common optional settings:
  - `rate`
  - `volume`
- Load path:
  - `load_tts_engine("pyttsx3")` returns `None` (lazy init at generation time).
- Generate path:
  - `generate_audio(..., "pyttsx3")` -> `generate_with_pyttsx3(...)` -> `pyttsx3.init().save_to_file(...)`

### StyleTTS2 (`styletts2`)
- Purpose: StyleTTS2 single-speaker cloning using selected model folder and reference file.
- Config source: `configs/tts_config.json` (`name: "StyleTTS2"`).
- Required settings:
  - `stts_model_path`
  - `stts_voice`
  - `stts_reference_audio_file`
- Common optional settings:
  - `stts_seed`
  - `stts_diffusion_steps`
  - `stts_alpha`
  - `stts_beta`
  - `stts_embedding_scale`
- Load path:
  - `load_tts_engine("styletts2")` -> `load_with_styletts2(...)` -> `styletts_api.inference.load.load_all_models(...)`
- Generate path:
  - `generate_audio(..., "styletts2")` -> `generate_with_styletts2(...)` -> `styletts_api.inference.generate.generate_audio(...)`

### XTTS (in progress) (`xtts`)
- Purpose: Placeholder for future XTTS integration.
- Config source: `configs/tts_config.json` (`name: "XTTS (in progress)"`).
- Status:
  - `load_with_xtts(...)` and `generate_with_xtts(...)` are placeholders in `src/tts_engines.py`.

### VibeVoice (`vibevoice`)
- Purpose: Voice-cloning TTS using VibeVoice model folders and voice sample folders.
- Config source: `configs/tts_config.json` (`name: "vibevoice"`).
- Required settings:
  - `vibevoice_model_path`
  - `vibevoice_voice`
- Common optional settings:
  - `vibevoice_device`
  - `vibevoice_ddpm_steps`
  - `vibevoice_num_speakers`
  - `vibevoice_cfg_scale`
  - `vibevoice_disable_cloning`
  - `vibevoice_seed`
- Load path:
  - `load_tts_engine("vibevoice")` -> `load_with_vibevoice(...)` -> `vibevoice.infer_api.VibeVoiceInferencer(...)`
- Generate path:
  - `generate_audio(..., "vibevoice")` -> `generate_with_vibevoice(...)` -> `VibeVoiceInferencer.generate_tts(...)` -> write output with `soundfile.write(...)`

### F5TTS (`f5tts`)
- Purpose: Reference-audio-guided TTS via `f5-tts` API.
- Config source: `configs/tts_config.json` (`name: "F5TTS"`).
- Required settings:
  - `f5tts_voice`
- Common optional settings:
  - `f5tts_model`
  - `f5tts_tokenizer`
  - `f5tts_vocoder`
  - `f5tts_duration_model`
  - `f5tts_speed`
  - `f5tts_seed`
- Load path:
  - `load_tts_engine("f5tts")` -> `load_with_f5tts(...)` -> `f5_tts.api.F5TTS(...)`
- Generate path:
  - `generate_audio(..., "f5tts")` -> `generate_with_f5tts(...)` -> `F5TTS.infer(...)`

### GPT-SoVITS (`gpt_sovits`)
- Purpose: GPT-SoVITS inference with versioned config/model pairing and voice prompt conditioning.
- Config source: `configs/tts_config.json` (`name: "GPT_SoVITS"`).
- Required settings:
  - `gpt_sovits_version`
  - `gpt_sovits_voice`
  - `gpt_sovits_ref_lang`
  - `gpt_sovits_output_lang`
- Common optional settings:
  - `gpt_sovits_model`
  - `gpt_sovits_vits_model`
  - `gpt_sovits_seed`
  - `gpt_sovits_speed`
  - `gpt_sovits_sample_steps`
  - `gpt_sovits_temperature`
  - `gpt_sovits_top_k`
  - `gpt_sovits_top_p`
- Load path:
  - `load_tts_engine("gpt_sovits")` -> `load_with_gpt_sovits(...)` -> `GPT_SoVITS.TTS_infer_pack.TTS.TTS(...)`
- Generate path:
  - `generate_audio(..., "gpt_sovits")` -> `generate_with_gpt_sovits(...)` -> `pipeline.run(inputs)` -> combine fragments -> `soundfile.write(...)`

## S2S Engines

### RVC (`rvc`)
- Purpose: Speech-to-speech voice conversion on generated audio files.
- Config source: `configs/s2s_config.json` (`name: "RVC"`).
- Required settings:
  - `selected_voice`
- Common optional settings:
  - `f0method`
  - `f0pitch`
  - `index_rate`
  - `filter_radius`
  - `resample_sr`
  - `rms_mix_rate`
  - `protect`
- Load path:
  - `load_s2s_engine("rvc")` -> `load_with_rvc(...)` -> `rvc_python.infer.RVCInference(...)` -> `load_model(selected_voice)`
- Process path:
  - `process_audio(..., "rvc", ...)` -> `process_with_rvc(...)` -> `s2s_engine.infer_file(...)`

## Related Files
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `src/controller.py`
- `src/model.py`
- `src/view.py`
- `configs/tts_config.json`
- `configs/s2s_config.json`
