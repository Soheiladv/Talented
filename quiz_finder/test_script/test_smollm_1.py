# test_smollm.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_ID = "HuggingFaceTB/SmolLM2-1.7B-Instruct"  # نسخه سبک‌تر: می‌تونی 360M رو امتحان کنی

def test():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to("cpu")
    prompt = (
        "You are an expert quiz designer. Generate 2 multiple-choice "
        "questions in Persian about ریاضی - جبر, difficulty متوسط.\n\n"
        "Output format must be strictly JSON: {\"questions\": [...]}"
    )
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    outputs = model.generate(input_ids, max_new_tokens=200, do_sample=False)
    print(tokenizer.decode(outputs[0], skip_special_tokens=True))

if __name__ == "__main__":
    test()
