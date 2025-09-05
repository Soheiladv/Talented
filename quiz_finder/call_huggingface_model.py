from turtle import st
from typing import Any, Dict

import torch
from pyparsing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM

from quiz_finder.view_gen3 import build_prompt, parse_llm_json, normalize_questions, call_huggingface_model, \
    generate_mock_quiz


def build_prompt_for_flant5(subject: str, topic: str, difficulty: str, num_questions: int) -> str:
    return (
        f"Generate {num_questions} multiple-choice questions in Persian for the subject '{subject}' on the topic '{topic}' at a '{difficulty}' difficulty level. "
        "Output only a valid JSON object with the structure: "
        '{"quiz": {"questions": [{"question_text": "...", "options": ["...", "...", "...", "..."], "correct_option_index": 0, "solution": "..."}]}}'
        "Ensure options array has exactly 4 items and correct_option_index is between 0 and 3."
    )




# تعریف گلوبال مدل و توکنایزر (فقط یک بار بارگذاری شوند)
@st.cache_resource
def load_mixtral_model(model_id: str, token: str):
    # بررسی وجود GPU و تنظیم device_map
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # برای کاهش مصرف حافظه، از bfloat16 یا float16 استفاده کنید
    # نیاز به PyTorch 1.10+ و GPU سازگار با bfloat16 برای بهترین عملکرد
    torch_dtype = torch.bfloat16 if device == "cuda" and torch.cuda.is_bf16_supported() else torch.float16 if device == "cuda" else torch.float32

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, token=token)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            device_map="auto", # برای تقسیم بار روی CPU/GPU
            token=token
        )
        return tokenizer, model
    except Exception as e:
        st.error(f"خطا در بارگذاری مدل Mixtral به صورت محلی: {e}. آیا منابع کافی دارید؟")
        return None, None

# بارگذاری مدل در شروع برنامه
import os
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()

if HUGGINGFACE_API_TOKEN and os.getenv("HUGGINGFACE_MODEL_ID"): # فرض می‌کنیم از MODEL_ID استفاده می‌کنید
    tokenizer, model = load_mixtral_model(os.getenv("HUGGINGFACE_MODEL_ID"), HUGGINGFACE_API_TOKEN)
    if tokenizer is None: # اگر بارگذاری مدل لوکال شکست خورد، به Inference API برگردید یا از سوالات نمونه استفاده کنید
        # می‌توانید اینجا HUGGINGFACE_MODEL را به یک مدل Inference API برگردانید
        # یا فقط اجازه دهید به generate_mock_quiz برسد
        st.session_state["use_local_model"] = False
    else:
        st.session_state["use_local_model"] = True
else:
    st.session_state["use_local_model"] = False


def call_local_huggingface_model(
        subject: str, topic: str, difficulty: str, num_questions: int) -> Optional[Dict[str, Any]]:
    if not st.session_state.get("use_local_model", False) or tokenizer is None or model is None:
        return None # Fallback به Inference API یا نمونه سوال

    prompt_text = build_prompt(subject, topic, difficulty, num_questions) # همان پرامپت قبلی

    messages = [
        {"role": "user", "content": prompt_text}
    ]

    try:
        inputs = tokenizer.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True).to(model.device)

        outputs = model.generate(
            inputs,
            max_new_tokens=1200,
            temperature=0.4,
            top_p=0.9,
            do_sample=True, # برای تنوع در پاسخ‌ها
            pad_token_id=tokenizer.eos_token_id # مهم برای جلوگیری از خطا
        )

        generated_text = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        parsed = parse_llm_json(generated_text)
        return parsed
    except Exception as e:
        st.error(f"خطا در تولید سوال با مدل محلی: {str(e)}")
        return None

def generate_quiz_service(
        subject: str, topic: str, difficulty: str, num_questions: int) -> Dict[str, Any]:
    if st.session_state.get("use_local_model", False):
        with st.spinner("در حال تولید سوالات با هوش مصنوعی محلی..."):
            ai_raw = call_local_huggingface_model(subject, topic, difficulty, num_questions)
            if ai_raw:
                normalized = normalize_questions(ai_raw)
                if normalized:
                    return {"success": True, "quiz": {"questions": normalized}}
            st.info("بارگذاری مدل محلی با شکست مواجه شد یا خطا داد. از سوالات نمونه استفاده می‌شود.")

    # اگر مدل محلی فعال نبود یا خطا داد، سعی کن از Inference API استفاده کنی (اگر توکن و مدل سازگار تنظیم شده)
    if HUGGINGFACE_API_TOKEN: # و مطمئن شوید HUGGINGFACE_MODEL به یک مدل Inference API سازگار تنظیم شده
         with st.spinner("در حال تولید سوالات با هوش مصنوعی (Hugging Face API)..."):
            ai_raw = call_huggingface_model(subject, topic, difficulty, num_questions) # تابع اصلی شما برای API
            if ai_raw:
                normalized = normalize_questions(ai_raw)
                if normalized:
                    return {"success": True, "quiz": {"questions": normalized}}
            st.warning("از سوالات نمونه استفاده می‌شود، زیرا اتصال به API یا تولید با شکست مواجه شد.")

    return generate_mock_quiz(subject, difficulty, num_questions)