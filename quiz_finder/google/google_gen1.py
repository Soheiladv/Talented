import os
import json
import random
import logging
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
from transformers import pipeline
from dotenv import load_dotenv

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "./distilgpt2").strip()  # مسیر مدل محلی

# تنظیمات صفحه
st.set_page_config(page_title="سازنده آزمون تیزهوشان", page_icon="🧠", layout="wide")
st.markdown("""
    <style>
        .main-header { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); color: white; padding: 2rem; border-radius: 15px; text-align: center; }
        .card { border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 1rem; }
        .btn-primary { background: #6a11cb; border: none; border-radius: 8px; }
        .option-btn { border: 1px solid #ddd; border-radius: 8px; padding: 0.5rem; margin: 0.5rem 0; }
        .correct-answer { background-color: #d4edda; border-color: #28a745; }
        .wrong-answer { background-color: #f8d7da; border-color: #dc3545; }
    </style>
""", unsafe_allow_html=True)

# مدل‌های موجود
MODEL_OPTIONS = {
    "./distilgpt2": {"name": "DistilGPT2 (خیلی سبک، ~300MB)", "size": "82M"},
    "./gpt-neo-125M": {"name": "GPT-Neo-125M (سبک، ~500MB)", "size": "125M"},
    "./phi-1_5": {"name": "Phi-1.5 (متوسط، ~2.8GB)", "size": "1.3B"}
}

# سوالات نمونه (Fallback)
SAMPLE_QUESTIONS = {
    "ریاضی": {
        "آسان": [
            {
                "question_text": "حاصل جمع ۶ و ۵ چیست؟",
                "options": ["۱۱", "۱۰", "۱۲", "۱۳"],
                "correct_option_index": 0,
                "solution": "۶ + ۵ = ۱۱"
            },
            {
                "question_text": "مساحت مربعی با ضلع ۴ چیست؟",
                "options": ["۱۲", "۱۶", "۲۰", "۸"],
                "correct_option_index": 1,
                "solution": "مساحت = ۴ × ۴ = ۱۶"
            }
        ],
        "متوسط": [
            {
                "question_text": "اگر ۴x = ۱۶ باشد، x چند است؟",
                "options": ["۳", "۴", "۵", "۶"],
                "correct_option_index": 1,
                "solution": "۴x = ۱۶ → x = ۴"
            }
        ],
        "سخت": [
            {
                "question_text": "عدد بعدی در دنباله ۱، ۳، ۶، ۱۰ چیست؟",
                "options": ["۱۲", "۱۴", "۱۵", "۱۶"],
                "correct_option_index": 2,
                "solution": "اختلاف‌ها: ۲، ۳، ۴ → عدد بعدی ۱۰ + ۵ = ۱۵"
            }
        ]
    },
    "علوم": {
        "آسان": [
            {
                "question_text": "کدام ماده مایع است؟",
                "options": ["یخ", "آب", "سنگ", "چوب"],
                "correct_option_index": 1,
                "solution": "آب حالت مایع دارد."
            }
        ],
        "متوسط": [
            {
                "question_text": "کدام سیاره بزرگ‌ترین در منظومه شمسی است؟",
                "options": ["زهره", "مریخ", "مشتری", "زحل"],
                "correct_option_index": 2,
                "solution": "مشتری بزرگ‌ترین سیاره است."
            }
        ]
    },
    "هوش": {
        "آسان": [
            {
                "question_text": "عدد بعدی در دنباله ۲، ۴، ۶ چیست؟",
                "options": ["۷", "۸", "۹", "۱۰"],
                "correct_option_index": 1,
                "solution": "اعداد زوج: ۲ + ۲ = ۴، ۴ + ۲ = ۶، ۶ + ۲ = ۸"
            }
        ],
        "متوسط": [
            {
                "question_text": "اگر A=۱ و B=۲ باشد، BA چند است؟",
                "options": ["۳", "۴", "۲", "۵"],
                "correct_option_index": 0,
                "solution": "B=۲، A=۱ → ۲ + ۱ = ۳"
            }
        ]
    }
}

# موضوعات دروس
SUBJECT_TOPICS = {
    "ریاضی": ["جبر", "هندسه", "اعداد", "الگوها"],
    "علوم": ["فیزیک", "شیمی", "زیست‌شناسی"],
    "هوش": ["استدلال منطقی", "الگویابی", "تصویری"]
}

# پایه‌های تحصیلی
GRADES = ["اول ابتدایی", "دوم ابتدایی", "سوم ابتدایی", "چهارم ابتدایی", "پنجم ابتدایی", "ششم ابتدایی"]


# توابع کمکی
def ensure_session_keys():
    defaults = {
        "quiz_started": False,
        "quiz_data": {"questions": []},
        "current_question": 0,
        "user_answers": [],
        "start_time": None,
        "selected_model": DEFAULT_MODEL
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def build_prompt(subject: str, topic: str, difficulty: str, grade: str, num_questions: int) -> str:
    return f"""
Generate {num_questions} multiple-choice questions for gifted students in Persian, for the subject "{subject}", topic "{topic}", difficulty level "{difficulty}", and grade level "{grade}". Each question must have exactly 4 options, a correct answer index (0-3), and a short explanation in Persian. Output only valid JSON, no extra text:
{{
  "quiz": {{
    "questions": [
      {{
        "question_text": "Question text in Persian",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_option_index": 0,
        "solution": "Short explanation in Persian"
      }}
    ]
  }}
}}
"""


def parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except:
        return None


def call_local_model(subject: str, topic: str, difficulty: str, grade: str, num_questions: int, model_name: str) -> \
Optional[Dict[str, Any]]:
    try:
        st.info(f"در حال بارگذاری مدل {model_name} و تولید سوالات...")
        logger.info(f"بارگذاری مدل {model_name}")
        generator = pipeline("text-generation", model=model_name, device=-1)  # device=-1 برای CPU
        prompt = build_prompt(subject, topic, difficulty, grade, num_questions)
        output = generator(prompt, max_new_tokens=500, temperature=0.6, top_p=0.9)
        parsed = parse_llm_json(output[0]["generated_text"])
        if parsed and "quiz" in parsed and parsed["quiz"].get("questions"):
            st.success("سوالات با موفقیت تولید شد!")
            return parsed
        st.warning("پاسخ معتبر دریافت نشد. از سوالات نمونه استفاده می‌شود.")
        return None
    except Exception as e:
        st.error(f"خطا در اجرای مدل محلی: {str(e)}")
        logger.error(f"خطای مدل محلی: {e}")
        return None


def generate_mock_quiz(subject: str, difficulty: str, num_questions: int) -> Dict[str, Any]:
    pool = SAMPLE_QUESTIONS.get(subject, {}).get(difficulty, [])
    if not pool:
        pool = [{"question_text": "سوال نمونه", "options": ["الف", "ب", "ج", "د"], "correct_option_index": 0,
                 "solution": "—"}]
    questions = random.sample(pool * num_questions, num_questions)
    return {"quiz": {"questions": questions}}


def generate_quiz(subject: str, topic: str, difficulty: str, grade: str, num_questions: int, model_name: str) -> Dict[
    str, Any]:
    result = call_local_model(subject, topic, difficulty, grade, num_questions, model_name)
    if result and "quiz" in result and result["quiz"].get("questions"):
        return result
    st.info("مدل محلی کار نکرد. از سوالات نمونه استفاده می‌شود.")
    return generate_mock_quiz(subject, difficulty, num_questions)


# رابط کاربری
def main():
    ensure_session_keys()

    # صفحه انتخاب مدل
    if "model_selected" not in st.session_state:
        st.session_state.model_selected = False

    if not st.session_state.model_selected:
        st.markdown(
            '<div class="main-header"><h1>انتخاب مدل برای تولید سوالات</h1><p>مدل سبک‌تر برای سرعت بیشتر و بدون نیاز به اینترنت</p></div>',
            unsafe_allow_html=True)
        st.header("مدل‌های موجود (دانلودشده)")
        for model_id, info in MODEL_OPTIONS.items():
            st.markdown(f"**{info['name']}** (اندازه: {info['size']})")
        selected_model = st.selectbox("انتخاب مدل", options=list(MODEL_OPTIONS.keys()),
                                      format_func=lambda x: MODEL_OPTIONS[x]["name"])
        if st.button("تأیید مدل", type="primary"):
            st.session_state.selected_model = selected_model
            st.session_state.model_selected = True
            st.rerun()
        return

    # صفحه اصلی
    st.markdown(
        '<div class="main-header"><h1>سازنده آزمون تیزهوشان</h1><p>سوالات استاندارد برای پایه‌های ابتدایی</p></div>',
        unsafe_allow_html=True)

    if not st.session_state.quiz_started:
        with st.sidebar:
            st.header("تنظیمات آزمون")
            grade = st.selectbox("پایه تحصیلی", GRADES)
            subject = st.selectbox("درس", list(SUBJECT_TOPICS.keys()))
            topic = st.selectbox("مبحث", SUBJECT_TOPICS[subject])
            difficulty = st.selectbox("سطح سختی", ["آسان", "متوسط", "سخت"])
            num_questions = st.slider("تعداد سوالات", 1, 3, 2)  # محدود به 3 برای سرعت
            if st.button("شروع آزمون", type="primary"):
                st.session_state.quiz_data = generate_quiz(subject, topic, difficulty, grade, num_questions,
                                                           st.session_state.selected_model)
                st.session_state.quiz_started = True
                st.session_state.user_answers = [None] * len(st.session_state.quiz_data["quiz"]["questions"])
                st.session_state.current_question = 0
                st.session_state.start_time = datetime.now()
                st.rerun()
    else:
        questions = st.session_state.quiz_data["quiz"]["questions"]
        current_q = st.session_state.current_question
        st.markdown(f'<div class="card"><h3>سوال {current_q + 1}: {questions[current_q]["question_text"]}</h3></div>',
                    unsafe_allow_html=True)

        for i, opt in enumerate(questions[current_q]["options"]):
            if st.button(opt, key=f"opt_{current_q}_{i}", use_container_width=True):
                st.session_state.user_answers[current_q] = i
                if current_q < len(questions) - 1:
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_started = False
                    st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            if current_q > 0 and st.button("قبلی"):
                st.session_state.current_question -= 1
                st.rerun()
        with col2:
            if st.button("نمایش نتایج", type="primary"):
                st.session_state.quiz_started = False
                st.rerun()

        if not st.session_state.quiz_started:
            correct_count = sum(
                1 for i, q in enumerate(questions) if st.session_state.user_answers[i] == q["correct_option_index"])
            st.markdown(f'<div class="card"><h2>نتایج: {correct_count}/{len(questions)} درست</h2></div>',
                        unsafe_allow_html=True)
            for i, q in enumerate(questions):
                is_correct = st.session_state.user_answers[i] == q["correct_option_index"]
                style = "correct-answer" if is_correct else "wrong-answer"
                st.markdown(
                    f'<div class="card"><h4>سوال {i + 1}: {q["question_text"]}</h4><p class="{style}">پاسخ شما: {q["options"][st.session_state.user_answers[i]]}</p><p>توضیح: {q["solution"]}</p></div>',
                    unsafe_allow_html=True)
            if st.button("آزمون جدید", type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.model_selected = False
                st.rerun()


if __name__ == "__main__":
    main()