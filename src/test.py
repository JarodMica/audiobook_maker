from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

# ---- Settings ----
model_path = "PaddlePaddle/PaddleOCR-VL"
image_path = "test.png"
task = "ocr" # Options: 'ocr' | 'table' | 'chart' | 'formula'
# ------------------

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PROMPTS = {
    "ocr": "OCR:",
    "table": "Table Recognition:",
    "formula": "Formula Recognition:",
    "chart": "Chart Recognition:",
}

image = Image.open(image_path).convert("RGB")

model = AutoModelForCausalLM.from_pretrained(
    model_path,  cache_dir="models/", trust_remote_code=True, torch_dtype=torch.bfloat16, revision="be8ed7492f996cb9e0148aa0c97567f2f7bddfc5"
).to(DEVICE).eval()
processor = AutoProcessor.from_pretrained(model_path, cache_dir="models/", trust_remote_code=True, revision="be8ed7492f996cb9e0148aa0c97567f2f7bddfc5")

messages = [
    {"role": "user",         
     "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": PROMPTS[task]},
        ]
    }
]
inputs = processor.apply_chat_template(
    messages, 
    tokenize=True, 
    add_generation_prompt=True, 	
    return_dict=True,
    return_tensors="pt"
).to(DEVICE)

outputs = model.generate(**inputs, max_new_tokens=1024)
outputs = processor.batch_decode(outputs, skip_special_tokens=True)[0]
print(outputs)
