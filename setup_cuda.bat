py -3.10 -m venv venv
call .\venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
venv\Scripts\python.exe -m pip install -r .\rvc\requirements.txt
venv\Scripts\python.exe -m pip install -r .\requirements.txt
venv\Scripts\python.exe -m pip install https://huggingface.co/Jmica/rvc/resolve/main/fairseq-0.12.2-cp310-cp310-win_amd64.whl
venv\Scripts\python.exe -m pip install git+https://github.com/JarodMica/rvc-tts-pipeline.git@lightweight#egg=rvc_tts_pipe
pause
