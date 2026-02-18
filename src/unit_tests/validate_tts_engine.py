import argparse
import json
import shutil
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _src_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _prepare_styletts2_voice(
    sample_dir: Path,
    voices_root: Path,
    voice_name: str,
) -> Path:
    src_wav = sample_dir / "test.wav"
    src_txt = sample_dir / "test.txt"
    if not src_wav.exists() or not src_txt.exists():
        raise FileNotFoundError(
            f"Missing test voice sample files in {sample_dir}. Expected test.wav and test.txt."
        )

    target_dir = voices_root / voice_name
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_wav, target_dir / "test.wav")
    shutil.copy2(src_txt, target_dir / "test.txt")
    return target_dir


def _default_styletts2_params(model_folder_name: str, voice_name: str) -> dict:
    return {
        "stts_model_path": model_folder_name,
        "stts_voice": voice_name,
        "stts_reference_audio_file": "test.wav",
        "stts_seed": -1,
        "stts_diffusion_steps": 20,
        "stts_alpha": 70,
        "stts_beta": 30,
        "stts_embedding_scale": 50,
    }


def _default_vibevoice_params(model_folder_name: str, voice_name: str) -> dict:
    return {
        "vibevoice_model_path": model_folder_name,
        "vibevoice_voice": voice_name,
        "vibevoice_device": "auto",
        "vibevoice_ddpm_steps": 10,
        "vibevoice_num_speakers": 1,
        "vibevoice_cfg_scale": 130,
        "vibevoice_disable_cloning": False,
        "vibevoice_seed": -1,
    }


def _load_json_params(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in params file, got {type(data).__name__}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Minimal terminal smoke test for TTS engine integration."
    )
    parser.add_argument(
        "--engine",
        default="styletts2",
        help="Engine dispatch name (currently validated path: styletts2).",
    )
    parser.add_argument(
        "--sample-dir",
        default="src/test_voice_sample",
        help="Directory with test.wav and test.txt for preparing voice samples.",
    )
    parser.add_argument(
        "--styletts-model-dir",
        default="engines/styletts/base",
        help="Path to StyleTTS2 model folder. Basename is used for stts_model_path.",
    )
    parser.add_argument(
        "--voice-name",
        default="validation_smoke",
        help="Voice folder name to create under voices/styletts for test assets.",
    )
    parser.add_argument(
        "--vibevoice-model-dir",
        default="engines/vibevoice/1.5v1_base",
        help="Path to VibeVoice model folder. Basename is used for vibevoice_model_path.",
    )
    parser.add_argument(
        "--vibevoice-voice-name",
        default="test",
        help="Voice folder name to read under voices/vibevoice for test assets.",
    )
    parser.add_argument(
        "--output",
        default="engine_smoke.wav",
        help="Output audio file path for generated smoke test audio.",
    )
    parser.add_argument(
        "--params-json",
        default="",
        help="Optional JSON file containing voice parameters override.",
    )
    parser.add_argument(
        "--text",
        default="This is a generic engine smoke test sentence.",
        help="Generic test sentence used for generation.",
    )
    args = parser.parse_args()

    repo = _repo_root()
    src = _src_root()
    sys.path.insert(0, str(src))

    engine_name = args.engine.lower()
    sample_dir = (repo / args.sample_dir).resolve()
    output_path = (repo / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    load_success = False
    returned_audio_path_pass = False
    file_size_pass = False
    returned_audio_path = None
    error_text = None

    try:
        import tts_engines  # pylint: disable=import-error

        if args.params_json:
            voice_params = _load_json_params((repo / args.params_json).resolve())
        elif engine_name == "styletts2":
            model_dir = (repo / args.styletts_model_dir).resolve()
            if not model_dir.exists():
                raise FileNotFoundError(f"StyleTTS model directory not found: {model_dir}")
            model_folder_name = model_dir.name

            voices_root = repo / "voices" / "styletts"
            _prepare_styletts2_voice(
                sample_dir=sample_dir,
                voices_root=voices_root,
                voice_name=args.voice_name,
            )
            voice_params = _default_styletts2_params(
                model_folder_name=model_folder_name,
                voice_name=args.voice_name,
            )
        elif engine_name == "vibevoice":
            model_dir = (repo / args.vibevoice_model_dir).resolve()
            if not model_dir.exists():
                raise FileNotFoundError(f"VibeVoice model directory not found: {model_dir}")
            model_folder_name = model_dir.name

            voice_dir = (repo / "voices" / "vibevoice" / args.vibevoice_voice_name).resolve()
            if not voice_dir.exists():
                raise FileNotFoundError(f"VibeVoice voice directory not found: {voice_dir}")

            voice_params = _default_vibevoice_params(
                model_folder_name=model_folder_name,
                voice_name=args.vibevoice_voice_name,
            )
        else:
            raise ValueError(
                f"Engine '{args.engine}' requires --params-json for now. "
                "Built-in default setup is currently provided for styletts2 and vibevoice."
            )

        tts_engine = tts_engines.load_tts_engine(engine_name, **voice_params)
        load_success = True

        returned_audio_path = tts_engines.generate_audio(
            tts_engine=tts_engine,
            sentence=args.text,
            voice_parameters=voice_params,
            tts_engine_name=engine_name,
            audio_path=str(output_path),
        )

        if isinstance(returned_audio_path, str) and returned_audio_path.strip():
            returned_audio_path_pass = True
        elif returned_audio_path:
            # Some engines may return truthy non-string success values.
            returned_audio_path_pass = True

        if output_path.exists() and output_path.stat().st_size > 0:
            file_size_pass = True

    except Exception as exc:  # pragma: no cover - smoke script
        error_text = str(exc)

    result = {
        "engine": engine_name,
        "checks": {
            "load_success": load_success,
            "returned_audio_path": returned_audio_path_pass,
            "output_file_nonempty": file_size_pass,
        },
        "score": f"{sum([load_success, returned_audio_path_pass, file_size_pass])}/3",
        "output_path": str(output_path),
        "returned_audio_path": returned_audio_path,
        "error": error_text,
    }
    print(json.dumps(result, indent=2))

    return 0 if all([load_success, returned_audio_path_pass, file_size_pass]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
