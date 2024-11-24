# tts_engines.py

'''
Note for sliders: Due to Qt6 sliders, to mimick decimal values, a "step" parameter is used so if a decimal value needs to be passed into some engine, the value passed from the voice settings needs to be divided by step.

For example, let's take "speed" from f5tts.  It needs to be a decimal value but Qt6 slider only allows for whole numbers  The tts_config has a step=100 with min=1 and max=200, so any value between those can be chosen.  Therefore, if the slider outputs 30, it should be 0.30 as round(30 / step, 2) = 0.30
'''

import os
import json

try:
    from tortoise_tts_api.inference.load import load_tts as load_tortoise_engine
    from tortoise_tts_api.inference.generate import generate as tortoise_generate
except Exception as e:
    print(f"Tortoise not available, received error: {e}")
    
try:
    from styletts_api.inference.load import load_all_models
    from styletts_api.inference.generate import generate_audio as stts_generate
except Exception as e:
    print(f"StyleTTS not available, received error: {e}")
try:
    from f5_tts.api import F5TTS
except Exception as e:
    print(f"F5-TTS is not available, received error: {e}")

def generate_audio(tts_engine, sentence, voice_parameters, tts_engine_name, audio_path):
    tts_engine_name = tts_engine_name.lower()
    if tts_engine_name == 'pyttsx3':
        return generate_with_pyttsx3(tts_engine, sentence, voice_parameters, audio_path)
    elif tts_engine_name == 'styletts2':
        return generate_with_styletts2(tts_engine, sentence, voice_parameters, audio_path)
    elif tts_engine_name == 'tortoise':
        return generate_with_tortoise(tts_engine, sentence, voice_parameters, audio_path)
    elif tts_engine_name == 'xtts':
        return generate_with_xtts(tts_engine, sentence, voice_parameters, audio_path)
    elif tts_engine_name == 'f5tts':
        return generate_with_f5tts(tts_engine, sentence, voice_parameters, audio_path)
    else:
        # Handle unknown engine
        return False

def generate_with_pyttsx3(tts_engine, sentence, voice_parameters, audio_path):
    import pyttsx3
    engine = pyttsx3.init()
    # Optionally set voice parameters here using voice_parameters
    # e.g., engine.setProperty('rate', voice_parameters.get('rate', 200))
    # Save the spoken sentence to an audio file
    engine.save_to_file(sentence, audio_path)
    engine.runAndWait()
    return os.path.exists(audio_path)

def generate_with_styletts2(tts_engine, sentence, voice_parameters, audio_path):
    engine_name = "StyleTTS2" 
    # Load the config and convert it to an object
    tts_config = load_config("configs/tts_config.json")
    tts_settings = dict_to_object(tts_config)

    styletts_engine_config = None
    for engine in tts_settings.tts_engines:
        if engine.name.lower() == engine_name.lower():  # Case-insensitive matching
            styletts_engine_config = engine
            break
        
    voice_root = next((param.folder_path for param in styletts_engine_config.parameters if param.attribute == "stts_voice"))

    voice = voice_parameters.get("stts_voice", None)
    if not voice:
        raise ("No voice found for StyleTTS")
    reference_audio_file = voice_parameters.get("stts_reference_audio_file")
    seed = int(voice_parameters.get("stts_seed"))
    if not seed:
        seed=-1
    diffusion_steps = voice_parameters.get("stts_diffusion_steps")
    
    alpha_step = next((param.step for param in styletts_engine_config.parameters if param.attribute=="stts_alpha"), 100)
    alpha = round(voice_parameters.get("stts_alpha", 70) / alpha_step, 2)
    
    beta_step = next((param.step for param in styletts_engine_config.parameters if param.attribute=="stts_beta"), 100)
    beta = round(voice_parameters.get("stts_beta", 30) / beta_step, 2)
    
    embedding_scale_step = next((param.step for param in styletts_engine_config.parameters if param.attribute=="stts_embedding_scale"), 100)
    embedding_scale = round(voice_parameters.get("stts_embedding_scale", 50) / embedding_scale_step, 2)
    
    audio_path = stts_generate(
        text=sentence, 
        voice=voice, 
        reference_audio_file=reference_audio_file, 
        seed=seed, 
        diffusion_steps=diffusion_steps, 
        alpha=alpha, 
        beta=beta, 
        embedding_scale=embedding_scale, 
        output_audio_path=audio_path,
        model_dict=tts_engine, 
        voices_root=voice_root
        )
    return audio_path

def generate_with_tortoise(tts_engine, sentence, voice_parameters, audio_path):
    if tts_engine is None:
        return False
    voice = voice_parameters.get('voice', 'random')
    sample_size = voice_parameters.get('sample_size', 4)
    use_hifigan = voice_parameters.get('use_hifigan', False)
    num_autoregressive_samples = sample_size

    result = tortoise_generate(
        tts=tts_engine,
        text=sentence,
        voice=voice,
        use_hifigan=use_hifigan,
        num_autoregressive_samples=num_autoregressive_samples,
        audio_path=audio_path
    )
    return os.path.exists(audio_path)

def generate_with_xtts(tts_engine, sentence, voice_parameters, audio_path):
    # Implement xtts TTS engine generation here
    pass

def generate_with_f5tts(tts_engine, sentence, voice_parameters, audio_path):
    engine_name = "f5tts"
    tts_settings = load_tts_config()
    f5tts_engine_config = find_engine_config(engine_name, tts_settings)
    
    voice_name = voice_parameters.get("f5tts_voice")
    ref_file_root = next((param.folder_path for param in f5tts_engine_config.parameters if param.attribute == "f5tts_voice" ))
    
    ref_file_path = os.path.join(ref_file_root, voice_name, f"{voice_name}.wav")
    ref_text = os.path.join(ref_file_root, voice_name, f"{voice_name}.txt")
    with open(ref_text, "r", encoding="utf-8") as f:
        ref_text = f.readline()
        
    seed = voice_parameters.get("f5tts_seed", -1)
    
    speed_step = next((param.step for param in f5tts_engine_config.parameters if param.attribute=="f5tts_speed"), 100)
    speed = round(voice_parameters.get("f5tts_speed") / speed_step, 2)
    print(speed)
        
    tts_engine.infer(
        ref_file=ref_file_path,
        ref_text=ref_text,
        gen_text=sentence,
        file_wave=audio_path,
        speed=speed,
        seed=seed
    )
    
    return audio_path
    
#################################################
############### Loading Functions ###############
#################################################                         

def load_tts_engine(tts_engine_name, **kwargs):
    tts_engine_name = tts_engine_name.lower()
    try:
        if tts_engine_name == 'pyttsx3':
            return None  # pyttsx3 doesn't require loading
        elif tts_engine_name == 'styletts2':
            return load_with_styletts2(**kwargs)
        elif tts_engine_name == 'tortoise':
            return load_with_tortoise(**kwargs)
        elif tts_engine_name == 'xtts':
            return load_with_xtts(**kwargs)
        elif tts_engine_name == "f5tts":
            return load_with_f5tts(**kwargs)
        else:
            # Handle unknown engine
            raise ValueError(f"Unknown TTS engine: {tts_engine_name}")
    except Exception as e:
        # Re-raise the exception to be caught by the worker thread
        raise e

def load_with_styletts2(**kwargs):
    engine_name = "StyleTTS2" 
    tts_settings = load_tts_config()
    styletts_engine_config = find_engine_config(engine_name, tts_settings)
    
    model_root = next((param.folder_path for param in styletts_engine_config.parameters if param.attribute == "stts_model_path"))
    model_folder_name = kwargs.get("stts_model_path")
    print(model_root)
    print(model_folder_name)
    folder_to_walk = os.path.join(model_root, model_folder_name)
    model_path = next(
        (os.path.join(folder_to_walk, file) for file in os.listdir(folder_to_walk) if file.endswith(".pth")),
        None
    )
    model_dict = load_all_models(model_path=model_path)
    return model_dict

def load_with_tortoise(**kwargs):
    engine_name = "Tortoise" 
    tts_settings = load_tts_config()
    tortoise_engine_config = find_engine_config(engine_name, tts_settings)
        
    # Find the folder paths for autoregressive model and tokenizer in the config
    ar_folder_path = next((param.folder_path for param in tortoise_engine_config.parameters if param.attribute == "autoregressive_model_path"), None)
    tokenizer_folder_path = next((param.folder_path for param in tortoise_engine_config.parameters if param.attribute == "tokenizer_json_path"), None)
    
    # Parameters needed to load the tortoise engine
    autoregressive_model_path = kwargs.get("autoregressive_model_path")
    if autoregressive_model_path:
        autoregressive_model_path = os.path.join(ar_folder_path, autoregressive_model_path)

    tokenizer_json_path = kwargs.get("tokenizer_json_path")
    if tokenizer_json_path:
        tokenizer_json_path = os.path.join(tokenizer_folder_path, tokenizer_json_path)
        
    diffusion_model_path = kwargs.get("diffusion_model_path", None)
    vocoder_name = kwargs.get("vocoder_name", None)
    use_deepspeed = kwargs.get("use_deepspeed", False)
    use_hifigan = kwargs.get("use_hifigan", False)
    

    tts = load_tortoise_engine(
        autoregressive_model_path=autoregressive_model_path,
        diffusion_model_path=diffusion_model_path,
        vocoder_name=vocoder_name,
        tokenizer_json_path=tokenizer_json_path,
        use_deepspeed=use_deepspeed,
        use_hifigan=use_hifigan
    )
    return tts

def load_with_xtts(**kwargs):
    # Implement loading for xtts TTS engine here
    pass

def load_with_f5tts(**kwargs):
    engine_name = "f5tts"
    tts_settings = load_tts_config()
    f5tts_engine_config = find_engine_config(engine_name, tts_settings)
    
    model_file = kwargs.get("f5tts_model")
    model_file_root = next((param.folder_path for param in f5tts_engine_config.parameters if param.attribute == "f5tts_model"))
    if model_file:
        model_file_path = os.path.join(model_file_root, model_file)
    else:
        model_file_path=""
        
    tokenizer = kwargs.get("f5tts_tokenizer")
    if tokenizer:
        tokenizer_root = next((param.folder_path for param in f5tts_engine_config.parameters if param.attribute == "f5tts_tokenizer"))
        tokenizer_path = os.path.join(tokenizer_root, tokenizer)
    else:
        tokenizer_path = ""
        
    vocos = kwargs.get("f5tts_vocoder", "vocos")
    vocos_local_path = next((param.folder_path for param in f5tts_engine_config.parameters if param.attribute == "f5tts_vocoder"))
    
    duration_model = kwargs.get("f5tts_duration_model", False)
    duration_model_path = next((param.folder_path for param in f5tts_engine_config.parameters if param.attribute == "f5tts_duration_model"))
    
    model = F5TTS(
        model_type="F5-TTS",
        ckpt_file=model_file_path,
        vocab_file=tokenizer_path,
        ode_method="euler",
        use_ema=True,
        vocoder_name=vocos,
        vocos_local_path=vocos_local_path,
        model_local_path=model_file_root,
        duration_model=duration_model,
        duration_model_path=duration_model_path,
        device="cuda"
    )
    return model

#################################################
############### Utility Functions ###############
#################################################

def find_engine_config(engine_name, tts_settings):
    for engine in tts_settings.tts_engines:
        if engine.name.lower() == engine_name.lower():
            engine_config = engine
            return engine_config

def load_tts_config(path="configs/tts_config.json"):
    tts_config = load_config(path)
    tts_settings = dict_to_object(tts_config)
    return tts_settings

def load_config(config_path):
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        return json.load(f)
    
# borrowed from https://github.com/ex3ndr/supervoice-gpt/blob/5c316bdbc7c70164ac4fe9a9a826976c4f546b0d/supervoice_gpt/misc.py#L4
# modified for lists
def dict_to_object(src):
    class DictToObject:
        def __init__(self, dictionary):
            for key, value in dictionary.items():
                # If value is a dictionary, convert it recursively
                if isinstance(value, dict):
                    value = DictToObject(value)
                # If value is a list, convert any dictionaries within the list recursively
                elif isinstance(value, list):
                    value = [DictToObject(item) if isinstance(item, dict) else item for item in value]
                self.__dict__[key] = value

        def __repr__(self):
            return f"{self.__dict__}"

    return DictToObject(src)
