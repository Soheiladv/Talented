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

# بارگذاری متغیرهای محیطی (اختیاری)
load_dotenv()

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

# سوالات نمونه (Fallback)
SAMPLE_QUESTIONS = {
    "ریاضی": {
        "آسان": [
            {
                "question_text": "حاصل جمع ۸ و ۴ چیست؟",
                "options": ["۱۲", "۱۱", "۱۳", "۱۴"],
                "correct_option_index": 0,
                "solution": "۸ + ۴ = ۱۲"
            },
            {
                "question_text": "مساحت مربعی با ضلع ۳ چیست؟",
                "options": ["۶", "۹", "۱۲", "۱۵"],
                "correct_option_index": 1,
                "solution": "مساحت = ۳ × ۳ = ۹"
            }
        ],
        "متوسط": [
            {
                "question_text": "اگر ۳x = ۱۲ باشد، x چند است؟",
                "options": ["۳", "۴", "۵", "۶"],
                "correct_option_index": 1,
                "solution": "۳x = ۱۲ → x = ۴"
            }
        ],
        "سخت": [
            {
                "question_text": "عدد بعدی در دنباله ۲، ۵، ۱۱، ۲۰ چیست؟",
                "options": ["۳۲", "۳۰", "۳۵", "۴۰"],
                "correct_option_index": 0,
                "solution": "اختلاف‌ها: ۳، ۶، ۹ → عدد بعدی ۲۰ + ۱۲ = ۳۲"
            }
        ]
    },
    "علوم": {
        "آسان": [
            {
                "question_text": "کدام ماده جامد است؟",
                "options": ["آب", "یخ", "بخار", "هوا"],
                "correct_option_index": 1,
                "solution": "یخ حالت جامد آب است."
            }
        ],
        "متوسط": [
            {
                "question_text": "کدام سیاره به خورشید نزدیک‌تر است؟",
                "options": ["زهره", "مریخ", "عطارد", "مشتری"],
                "correct_option_index": 2,
                "solution": "عطارد نزدیک‌ترین سیاره به خورشید است."
            }
        ]
    },
    "هوش": {
        "آسان": [
            {
                "question_text": "عدد بعدی در دنباله ۱، ۳، ۵ چیست؟",
                "options": ["۶", "۷", "۸", "۹"],
                "correct_option_index": 1,
                "solution": "اعداد فرد: ۱ + ۲ = ۳، ۳ + ۲ = ۵، ۵ + ۲ = ۷"
            }
        ],
        "متوسط": [
            {
                "question_text": "اگر A=۱ و B=۲ باشد، AB چند است؟",
                "options": ["۳", "۴", "۲", "۱"],
                "correct_option_index": 0,
                "solution": "A=۱، B=۲ → ۱ + ۲ = ۳"
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
        "start_time": None
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


def call_local_model(subject: str, topic: str, difficulty: str, grade: str, num_questions: int) -> Optional[
    Dict[str, Any]]:
    try:
        st.info("در حال بارگذاری مدل محلی و تولید سوالات...")
        logger.info("بارگذاری مدل google/gemma-2-2b-it")
        generator = pipeline("text-generation", model="google/gemma-2-2b-it", device=-1)  # device=-1 برای CPU
        prompt = build_prompt(subject, topic, difficulty, grade, num_questions)
        output = generator(prompt, max_new_tokens=1000, temperature=0.5, top_p=0.9)
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


def generate_quiz(subject: str, topic: str, difficulty: str, grade: str, num_questions: int) -> Dict[str, Any]:
    result = call_local_model(subject, topic, difficulty, grade, num_questions)
    if result and "quiz" in result and result["quiz"].get("questions"):
        return result
    st.info("مدل محلی کار نکرد. از سوالات نمونه استفاده می‌شود.")
    return generate_mock_quiz(subject, difficulty, num_questions)


# رابط کاربری
def main():
    ensure_session_keys()
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
            num_questions = st.slider("تعداد سوالات", 1, 10, 5)
            if st.button("شروع آزمون", type="primary"):
                st.session_state.quiz_data = generate_quiz(subject, topic, difficulty, grade, num_questions)
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
                st.rerun()


if __name__ == "__main__":
    main()