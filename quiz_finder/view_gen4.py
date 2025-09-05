import os
import json
import random
import logging
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from dotenv import load_dotenv

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.2-3B-Instruct").strip()
HUGGINGFACE_TIMEOUT = int(os.getenv("HUGGINGFACE_TIMEOUT", "30"))

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
        "آسان": [{"question_text": "حاصل ۵ + ۷ چیست؟", "options": ["۱۲", "۱۱", "۱۳", "۱۴"], "correct_option_index": 0,
                  "solution": "۵ + ۷ = ۱۲"}],
        "متوسط": [
            {"question_text": "اگر ۲x = ۱۰ باشد، x چیست؟", "options": ["۴", "۵", "۶", "۷"], "correct_option_index": 1,
             "solution": "۲x = ۱۰ → x = ۵"}],
    },
    "علوم": {
        "آسان": [{"question_text": "کدام سیاره به خورشید نزدیک‌تر است؟", "options": ["زهره", "مریخ", "عطارد", "مشتری"],
                  "correct_option_index": 2, "solution": "عطارد نزدیک‌ترین است."}],
    }
}

# موضوعات دروس
SUBJECT_TOPICS = {"ریاضی": ["جبر", "هندسه"], "علوم": ["فیزیک", "شیمی"]}


# توابع کمکی
def ensure_session_keys():
    defaults = {"quiz_started": False, "quiz_data": {"questions": []}, "current_question": 0, "user_answers": [],
                "start_time": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def build_prompt(subject: str, topic: str, difficulty: str, num_questions: int) -> str:
    return f"""
You are an expert in creating educational quizzes. Generate {num_questions} multiple-choice questions for the subject "{subject}", topic "{topic}", and difficulty level "{difficulty}". Each question must have exactly 4 options, a correct answer index (0-3), and a short explanation. Output only valid JSON, no extra text:
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


def call_huggingface_model(subject: str, topic: str, difficulty: str, num_questions: int) -> Optional[Dict[str, Any]]:
    if not HUGGINGFACE_API_TOKEN:
        st.warning("توکن HuggingFace تنظیم نشده است.")
        return None
    url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}", "Content-Type": "application/json"}
    prompt = build_prompt(subject, topic, difficulty, num_questions)
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 1000, "temperature": 0.5, "top_p": 0.9, "return_full_text": False},
        "options": {"use_cache": True, "wait_for_model": True}
    }
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

    try:
        st.info(f"در حال تولید سوالات با {HUGGINGFACE_MODEL}...")
        logger.info(f"ارسال درخواست به {url}")
        resp = session.post(url, headers=headers, json=payload, timeout=HUGGINGFACE_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data and "generated_text" in data[0]:
            parsed = parse_llm_json(data[0]["generated_text"])
            if parsed:
                st.success("سوالات تولید شد!")
                return parsed
        st.warning("پاسخ معتبر دریافت نشد.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"زمان پاسخ ({HUGGINGFACE_TIMEOUT} ثانیه) تمام شد.")
        logger.error("Timeout")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"خطای HTTP: {e}")
        logger.error(f"HTTP Error: {e}")
        return None
    except Exception as e:
        st.error(f"خطا: {str(e)}")
        logger.error(f"Error: {e}")
        return None


def generate_mock_quiz(subject: str, difficulty: str, num_questions: int) -> Dict[str, Any]:
    pool = SAMPLE_QUESTIONS.get(subject, {}).get(difficulty, [])
    if not pool:
        pool = [{"question_text": "سوال نمونه", "options": ["الف", "ب", "ج", "د"], "correct_option_index": 0,
                 "solution": "—"}]
    questions = random.sample(pool * num_questions, num_questions)
    return {"quiz": {"questions": questions}}


def generate_quiz(subject: str, topic: str, difficulty: str, num_questions: int) -> Dict[str, Any]:
    result = call_huggingface_model(subject, topic, difficulty, num_questions)
    if result and "quiz" in result and result["quiz"].get("questions"):
        return result
    st.info("API در دسترس نبود. از سوالات نمونه استفاده می‌شود.")
    return generate_mock_quiz(subject, difficulty, num_questions)


# رابط کاربری
def main():
    ensure_session_keys()
    st.markdown('<div class="main-header"><h1>سازنده آزمون تیزهوشان</h1></div>', unsafe_allow_html=True)

    if not st.session_state.quiz_started:
        with st.sidebar:
            st.header("تنظیمات آزمون")
            subject = st.selectbox("درس", list(SUBJECT_TOPICS.keys()))
            topic = st.selectbox("مبحث", SUBJECT_TOPICS[subject])
            difficulty = st.selectbox("سطح سختی", ["آسان", "متوسط", "سخت"])
            num_questions = st.slider("تعداد سوالات", 1, 10, 5)
            if st.button("شروع آزمون", type="primary"):
                st.session_state.quiz_data = generate_quiz(subject, topic, difficulty, num_questions)
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


if __name__ == "__main__":
    main()