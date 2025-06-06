# s2s_engines.py
import os
import json
import torch
import traceback

try:
    from rvc_python.infer import RVCInference
    import fairseq
except Exception as e:
    print(f"RVC not installed, received error: {e}")
    print("Full traceback:")
    traceback.print_exc()

def process_audio(s2s_engine, s2s_engine_name, input_audio_path, output_audio_path, parameters):
    s2s_engine_name = s2s_engine_name.lower()
    if s2s_engine_name == 'rvc':
        return process_with_rvc(s2s_engine, input_audio_path, output_audio_path)
    # Add other s2s engines here
    else:
        print(f"s2s engine '{s2s_engine_name}' not recognized.")
        return False

def process_with_rvc(s2s_engine, input_audio_path, output_audio_path):
    s2s_engine.infer_file(input_audio_path, output_audio_path)
    return output_audio_path

def load_s2s_engine(s2s_engine_name, **kwargs):
    s2s_engine_name = s2s_engine_name.lower()
    try:
        if s2s_engine_name == 'rvc':
            return load_with_rvc(**kwargs)
        else:
            # Handle unknown engine
            raise ValueError(f"Unknown TTS engine: {s2s_engine_name}")
    except Exception as e:
        # Re-raise the exception to be caught by the worker thread
        raise e
    
def load_with_rvc(**kwargs):
    engine_name = "RVC"
    s2s_config = load_config("configs/s2s_config.json")
    s2s_settings = dict_to_object(s2s_config)
    
    rvc_engine_config = None
    for engine in s2s_settings.s2s_engines:
        if engine.name.lower() == engine_name.lower():
            rvc_engine_config = engine
            break
        
    rvc_folder_path = next((param.folder_path for param in rvc_engine_config.parameters if param.attribute == "selected_voice"), None)
    
    f0method = kwargs.get("f0method")
    f0up_key = kwargs.get("f0pitch")
    
    index_step = next((param.step for param in rvc_engine_config.parameters if param.attribute == "index_rate"), 100)
    index_rate = kwargs.get("index_rate")/index_step
    
    filter_radius = kwargs.get("filter_radius")
    resample_sr = int(str(kwargs.get("resample_sr", "0:")).split(":")[0])
    
    rms_mix_rate_step = next((param.step for param in rvc_engine_config.parameters if param.attribute == "rms_mix_rate"), 100)
    rms_mix_rate = kwargs.get("rms_mix_rate")/rms_mix_rate_step
    
    protect_step = next((param.step for param in rvc_engine_config.parameters if param.attribute == "protect"), 100)
    protect = kwargs.get("protect")/protect_step
    

    torch.serialization.add_safe_globals([fairseq.data.dictionary.Dictionary])
    s2s = RVCInference(models_dir=rvc_folder_path,
                       device="cuda:0",
                       f0method=f0method,
                       f0up_key=f0up_key,
                       index_rate=index_rate,
                       filter_radius=filter_radius,
                       resample_sr=resample_sr,
                       rms_mix_rate=rms_mix_rate,
                       protect=protect
                       )
    voice_to_use = kwargs.get("selected_voice", None)
    if voice_to_use == None:
        return
    
    s2s.load_model(voice_to_use)
    return s2s

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