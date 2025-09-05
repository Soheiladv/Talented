# ===== IMPORTS & DEPENDENCIES =====
import os
import re
import json
import time
import logging

logger = logging.getLogger(__name__)

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

# ===== CONFIGURATION & CONSTANTS =====
# تنظیمات صفحه
st.set_page_config(
    page_title="سازنده سوالات تیزهوشان",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Bootstrap & Icons
st.markdown(
    """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<style>
    .main-header { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
    .card { border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s; margin-bottom: 1.5rem; border: none; }
    .card:hover { transform: translateY(-5px); }
    .card-header { border-radius: 15px 15px 0 0 !important; font-weight: 600; }
    .btn-primary { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        border: none; border-radius: 8px; padding: 0.7rem 1.5rem; font-weight: 600; }
    .btn-primary:hover { background: linear-gradient(135deg, #5a0db9 0%, #1c65e0 100%);
        transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .option-btn { text-align: right; direction: rtl; margin: 0.5rem 0; transition: all 0.3s;
        border: 2px solid #e9ecef; border-radius: 10px; padding: 1rem; width: 100%; }
    .option-btn:hover { background-color: #f8f9fa; border-color: #6a11cb; }
    .correct-answer { background-color: #d4edda !important; border-color: #28a745 !important; color: #155724; }
    .wrong-answer { background-color: #f8d7da !important; border-color: #dc3545 !important; color: #721c24; }
    .progress-bar { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); }
    .timer-container { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white; border-radius: 15px; padding: 1rem; margin-bottom: 1.5rem; }
    .question-number { background: #6a11cb; color: white; width: 40px; height: 40px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-left: 10px; }
    .option-label { background: #6a11cb; color: white; width: 30px; height: 30px;
        border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; 
        font-weight: bold; margin-left: 10px; }
</style>
""",
    unsafe_allow_html=True,
)

# بارگذاری متغیرهای محیطی
load_dotenv()

HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2").strip()

## FIX: Ensure the timeout is converted to an integer here ##
HUGGINGFACE_TIMEOUT = int(os.getenv("HUGGINGFACE_TIMEOUT", "120"))

print("HF Token:", "Loaded" if HUGGINGFACE_API_TOKEN else "NOT FOUND", "HUGGINGFACE_MODEL IS:", HUGGINGFACE_MODEL)


# موضوعات پیشنهادی برای هر درس
SUBJECT_TOPICS: Dict[str, List[str]] = {
    "ریاضی": ["جبر", "هندسه", "احتمال", "آمار", "عدد و عملیات"],
    "علوم": ["فیزیک", "شیمی", "زیست‌شناسی", "زمین‌شناسی", "نجوم"],
    "هوش": ["استدلال منطقی", "الگویابی", "حل مسئله", "تصویری", "کلامی"],
}

# ===== SAMPLE QUESTIONS (Fallback) =====
SAMPLE_QUESTIONS: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "ریاضی": {
        "آسان": [
            {
                "question_text": "حاصل جمع ۱۵ و ۲۳ چیست؟",
                "options": ["۳۸", "۳۷", "۳۹", "۴۰"],
                "correct_option_index": 0,
                "solution": "۱۵ + ۲۳ = ۳۸",
            },
            {
                "question_text": "مساحت مربعی با ضلع ۵ سانتیمتر چقدر است؟",
                "options": ["۲۰ سانتیمتر مربع", "۲۵ سانتیمتر مربع", "۱۰ سانتیمتر مربع", "۱۵ سانتیمتر مربع"],
                "correct_option_index": 1,
                "solution": "مساحت مربع = ۵ × ۵ = ۲۵",
            },
        ],
        "متوسط": [
            {
                "question_text": "اگر ۲x + ۵ = ۱۵ باشد، مقدار x چقدر است؟",
                "options": ["۵", "۱۰", "۷", "۸"],
                "correct_option_index": 0,
                "solution": "۲x = ۱۵ - ۵ → x = ۵",
            },
        ],
        "سخت": [
            {
                "question_text": "در مثلث قائم‌الزاویه، وتر ۱۰ و یکی از اضلاع ۶ است. ضلع دیگر؟",
                "options": ["۸", "۷", "۹", "۱۰"],
                "correct_option_index": 0,
                "solution": "۶² + b² = ۱۰² → b=۸",
            },
        ],
    },
    "علوم": {
        "آسان": [
            {
                "question_text": "کدام گزینه از منابع انرژی تجدیدپذیر است؟",
                "options": ["نفت", "زغال سنگ", "انرژی خورشیدی", "گاز طبیعی"],
                "correct_option_index": 2,
                "solution": "خورشیدی تجدیدپذیر است.",
            },
        ],
        "متوسط": [
            {
                "question_text": "کدام سلول در سیستم ایمنی بدن مسئول تولید پادتن است؟",
                "options": ["گلبول قرمز", "پلاکت", "لنفوسیت B", "لنفوسیت T"],
                "correct_option_index": 2,
                "solution": "B-Cell پادتن می‌سازد.",
            },
        ],
        "سخت": [
            {
                "question_text": "در کدام مرحله از میوز، تبادل مواد ژنتیکی رخ می‌دهد؟",
                "options": ["پروفاز I", "متافاز I", "آنافاز I", "تلوفاز I"],
                "correct_option_index": 0,
                "solution": "کراسینگ‌اور در پروفاز I.",
            },
        ],
    },
    "هوش": {
        "آسان": [
            {
                "question_text": "عدد بعدی در دنباله ۲, ۴, ۶, ۸, ... چیست؟",
                "options": ["۱۰", "۱۲", "۱۴", "۱۶"],
                "correct_option_index": 0,
                "solution": "اعداد زوج.",
            },
        ],
        "متوسط": [
            {
                "question_text": "اگر A=1, B=2, C=3 باشد، CAT چند می‌شود؟",
                "options": ["۲۴", "۲۰", "۱۸", "۱۵"],
                "correct_option_index": 0,
                "solution": "C=3, A=1, T=20 → 24",
            },
        ],
        "سخت": [
            {
                "question_text": "اگر ۵ ماشین ۵ دقیقه برای ۵ دستگاه لازم دارند، ۱۰۰ ماشین برای ۱۰۰ دستگاه چقدر؟",
                "options": ["۵", "۱۰", "۲۰", "۱۰۰"],
                "correct_option_index": 0,
                "solution": "هر ماشین ۵ دقیقه/دستگاه → ۵ دقیقه.",
            },
        ],
    },
}


# ===== UTILITY FUNCTIONS =====
def persian_digits_to_english(s: str) -> str:
    mapping = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return s.translate(mapping)


def clamp(n: int, min_n: int, max_n: int) -> int:
    return max(min_n, min(n, max_n))


def ensure_session_keys():
    defaults = {
        "quiz_started": False,
        "quiz_finished": False,
        "quiz_data": {"questions": []},
        "current_question": 0,
        "user_answers": [],
        "start_time": None,
        "time_limit_seconds": 0,
        "quiz_subject": "",
        "quiz_topic": "",
        "quiz_difficulty": "",
        "quiz_grade": "",
    }
    logger.info(f'ensure_session_keys s')
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def safe_questions_list(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        q = result.get("quiz", {}).get("questions", [])
        return q if isinstance(q, list) else []
    except Exception:
        return []


# ===== CORE BUSINESS LOGIC / SERVICES =====
def build_prompt(subject: str, topic: str, difficulty: str, num_questions: int) -> str:
    # فرمت پرامپت برای Mistral Instruct models
    base_prompt = (
        f"برای درس «{subject}» و مبحث «{topic}» با سطح «{difficulty}»، "
        f"{num_questions} سؤال چهارگزینه‌ای استاندارد تولید کن. "
        "خروجی را فقط به صورت JSON معتبر زیر بده و هیچ متن اضافه‌ای ننویس:\n\n"
        "{\n"
        '  "quiz": {\n'
        '    "questions": [\n'
        '      {\n'
        '        "question_text": "متن سوال",\n'
        '        "options": ["گزینه ۱","گزینه ۲","گزینه ۳","گزینه ۴"],\n'
        '        "correct_option_index": 0,\n'
        '        "solution": "توضیح راه‌حل کوتاه"\n'
        "      }\n"
        "    ]\n"
        "  }\n"
        "}\n"
        "حتماً مطمئن شو که آرایه options دقیقاً ۴ گزینه دارد و correct_option_index عددی بین ۰ تا ۳ است."
    )
    import logging
    logging.info(f'base_prompt')
    return f"<s>[INST] {base_prompt} [/INST]"  # افزودن توکن‌های مخصوص Mistral


def parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    start_idxs = [m.start() for m in re.finditer(r"\{", text)]
    for si in start_idxs:
        depth = 0
        for ei in range(si, len(text)):
            if text[ei] == "{":
                depth += 1
            elif text[ei] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[si: ei + 1]
                    try:
                        data = json.loads(candidate)
                        return data
                    except Exception:
                        continue
    try:
        data = json.loads(persian_digits_to_english(text))
        return data
    except Exception:
        return None


# def call_huggingface_model(
#     subject: str, topic: str, difficulty: str, num_questions: int) -> Optional[Dict[str, Any]]:
#     if not HUGGINGFACE_API_TOKEN or not HUGGINGFACE_MODEL:
#         st.warning("توکن HuggingFace تنظیم نشده است. از سوالات نمونه استفاده می‌شود.")
#         return None
#
#     url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
#     headers = {
#         "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
#         "Content-Type": "application/json",
#     }
#     prompt = build_prompt(subject, topic, difficulty, num_questions)
#     payload = {
#         "inputs": prompt,
#         "parameters": {
#             "max_new_tokens": 1200,
#             "temperature": 0.4,
#             "top_p": 0.9,
#             "return_full_text": False,
#         },
#         "options": {"use_cache": True, "wait_for_model": True},
#     }
#     # --- FIX: بررسی دقیق پاسخ سرور ---
#     try:
#
#         st.info(f"🚀 در حال ارسال درخواست به مدل {HUGGINGFACE_MODEL}...")
#         print(f"🚀 Sending request to Hugging Face API: {url}")  # لاگ در ترمینال
#
#         resp = requests.post(url, headers=headers, json=payload, timeout=HUGGINGFACE_TIMEOUT)
#         if resp.status_code == 200:
#             st.success("✅ پاسخ با موفقیت از سرور دریافت شد. در حال پردازش...")
#             print("✅ Response received successfully.")
#         else:
#             # نمایش خطای سرور به کاربر
#             st.error(f"❌ سرور Hugging Face با خطای {resp.status_code} پاسخ داد.")
#             print(f"❌ Hugging Face server responded with error {resp.status_code}.")
#
#             # نمایش توضیحات بیشتر برای خطاهای رایج
#             if resp.status_code == 401:
#                 st.warning("خطای 401: توکن API شما نامعتبر است. لطفاً آن را در فایل .env بررسی کنید.")
#             elif resp.status_code == 404:
#                 st.warning("خطای 404: مدل پیدا نشد. مطمئن شوید به این مدل دسترسی دارید و نام آن صحیح است.")
#             elif resp.status_code == 503:
#                 st.warning(
#                     "خطای 503: مدل در حال حاضر در دسترس نیست یا در حال بارگذاری است. لطفاً چند دقیقه دیگر دوباره تلاش کنید.")
#
#             print("Server Response:", resp.text)  # چاپ پاسخ کامل خطا در ترمینال
#             return None
#
#         data = resp.json()
#         if isinstance(data, list) and data and "generated_text" in data[0]:
#             parsed = parse_llm_json(data[0]["generated_text"])
#             st.info("🧠 پاسخ هوش مصنوعی پردازش شد.")
#             return parsed
#             #
#             # if "quiz" in data:
#             #     return data
#             # if "generated_text" in data:
#             #     parsed = parse_llm_json(data["generated_text"])
#             #     return parsed
#         parsed = parse_llm_json(json.dumps(data, ensure_ascii=False))
#         return parsed
#     except requests.exceptions.Timeout:
#         st.error("❌ زمان پاسخگویی سرور به پایان رسید (Timeout). لطفاً دوباره تلاش کنید.")
#         print("❌ Request timed out.")
#         return None
#     except requests.exceptions.RequestException as e:
#         st.error(f"❌ خطا در اتصال به شبکه: {str(e)}")
#         st.exception(e)  # نمایش کامل خطا در رابط کاربری برای دیباگ
#         print(f"❌ Network connection error: {e}")
#         return None
#     except Exception as e:
#         st.error(f"❌ خطا در پردازش پاسخ: {str(e)}")
#         st.exception(e)
#         print(f"❌ Error during response processing: {e}")
#         return None
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests
import streamlit as st
import logging

def call_huggingface_model(subject: str, topic: str, difficulty: str, num_questions: int) -> Optional[Dict[str, Any]]:
    if not HUGGINGFACE_API_TOKEN or not HUGGINGFACE_MODEL:
        st.warning("توکن یا مدل HuggingFace تنظیم نشده است. از سوالات نمونه استفاده می‌شود.")
        return None

    url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}", "Content-Type": "application/json"}
    prompt = build_prompt(subject, topic, difficulty, num_questions)
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 1200, "temperature": 0.4, "top_p": 0.9, "return_full_text": False},
        "options": {"use_cache": True, "wait_for_model": True},
    }

    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    try:
        st.info(f"🚀 در حال ارسال درخواست به مدل {HUGGINGFACE_MODEL}...")
        logging.info(f"ارسال درخواست به {url}")
        resp = session.post(url, headers=headers, json=payload, timeout=HUGGINGFACE_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data and "generated_text" in data[0]:
            parsed = parse_llm_json(data[0]["generated_text"])
            if parsed:
                st.success("🧠 سوالات با موفقیت تولید شد.")
                return parsed
        st.warning("پاسخ معتبر دریافت نشد. از نمونه‌ها استفاده می‌شود.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"❌ زمان پاسخگویی ({HUGGINGFACE_TIMEOUT} ثانیه) به پایان رسید.")
        logging.error("درخواست Timeout شد.")
        return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"❌ خطای HTTP: {http_err}. کد وضعیت: {resp.status_code}")
        if resp.status_code == 504:
            st.info("سرور در حال بارگذاری مدل است. چند دقیقه صبر کنید و دوباره تلاش کنید.")
        logging.error(f"خطای HTTP: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        st.error(f"❌ خطای شبکه: {req_err}")
        logging.error(f"خطای درخواست: {req_err}")
        return None
    except Exception as e:
        st.error(f"❌ خطای پردازش: {str(e)}")
        logging.error(f"خطای پردازش: {e}")
        return None
def normalize_questions(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    questions = []
    items = raw.get("quiz", {}).get("questions", []) if isinstance(raw, dict) else []
    if not isinstance(items, list):
        return []

    for item in items:
        try:
            qt = str(item.get("question_text", "")).strip()
            opts = list(item.get("options", []))[:4]
            if len(opts) < 4:
                while len(opts) < 4:
                    opts.append(f"گزینه {len(opts) + 1}")
            ci = int(item.get("correct_option_index", 0))
            ci = clamp(ci, 0, 3)
            sol = str(item.get("solution", "")).strip() or "بدون توضیح"

            if not qt:
                continue

            questions.append(
                {
                    "question_text": qt,
                    "options": opts[:4],
                    "correct_option_index": ci,
                    "solution": sol,
                }
            )
        except Exception:
            continue

    return questions


def generate_mock_quiz(subject: str, difficulty: str, num_questions: int) -> Dict[str, Any]:
    pool = SAMPLE_QUESTIONS.get(subject, {}).get(difficulty, [])
    if not pool:
        for subj in SAMPLE_QUESTIONS.values():
            for arr in subj.values():
                pool.extend(arr)

    if not pool:
        pool = [
            {
                "question_text": "نمونه سوال در دسترس نیست. این یک سوال نمونه است.",
                "options": ["الف", "ب", "ج", "د"],
                "correct_option_index": 0,
                "solution": "—",
            }
        ]

    questions = []
    while len(questions) < num_questions:
        random.shuffle(pool)
        for q in pool:
            questions.append(q.copy())
            if len(questions) >= num_questions:
                break

    for q in questions:
        opts = q["options"]
        correct_idx = q["correct_option_index"]
        correct_val = opts[correct_idx]
        random.shuffle(opts)
        q["options"] = opts
        q["correct_option_index"] = opts.index(correct_val)

    return {"quiz": {"questions": questions}, "success": True}


def generate_quiz_service(
        subject: str, topic: str, difficulty: str, num_questions: int
) -> Dict[str, Any]:
    if HUGGINGFACE_API_TOKEN:
        with st.spinner("در حال تولید سوالات با هوش مصنوعی..."):
            ai_raw = call_huggingface_model(subject, topic, difficulty, num_questions)
            if ai_raw:
                normalized = normalize_questions(ai_raw)
                if normalized:
                    return {"success": True, "quiz": {"questions": normalized}}
            st.info("از سوالات نمونه استفاده می‌شود.")

    return generate_mock_quiz(subject, difficulty, num_questions)


# ===== FRONTEND (Streamlit) =====
def main():
    ensure_session_keys()
    st.markdown(
        """
    <div class="main-header text-center">
        <h1><i class="bi bi-lightbulb"></i> سازنده سوالات تیزهوشان</h1>
        <p class="lead">پلتفرم هوشمند تولید سوالات استاندارد با هوش مصنوعی + fallback امن</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    logging.info(f'result Step 1 : {st.markdown}')

    if not st.session_state.quiz_started or not safe_questions_list(st.session_state.quiz_data):
        logging.info(f'Step st.session_state.quiz_started is None')
        with st.sidebar:
            st.markdown(
                """
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <i class="bi bi-gear"></i> تنظیمات آزمون
                </div>
                <div class="card-body">
            """,
                unsafe_allow_html=True,
            )

            grade = st.selectbox(
                "پایه تحصیلی",
                ["سوم ابتدایی", "چهارم ابتدایی", "پنجم ابتدایی", "ششم ابتدایی", "هفتم", "هشتم", "نهم"],
            )

            subject = st.selectbox("درس", list(SUBJECT_TOPICS.keys()))
            topic = st.selectbox("مبحث", SUBJECT_TOPICS[subject])

            difficulty = st.select_slider("سطح سختی", options=["آسان", "متوسط", "سخت"])
            num_questions = st.slider("تعداد سوالات", min_value=3, max_value=20, value=5)

            per_q_seconds = st.slider("زمان هر سؤال (ثانیه)", min_value=30, max_value=180, value=90, step=10)

            if st.button("شروع آزمون", type="primary", use_container_width=True):
                result = generate_quiz_service(subject, topic, difficulty, num_questions)
                logging.info(f'result Step 1 : {result}')
                questions = safe_questions_list(result)
                logging.info(f'questions Step 1 : {questions}')
                if not questions:
                    st.error("خطا در تولید سوال. لطفاً مجدد تلاش کنید.")
                else:
                    st.session_state.quiz_data = {"questions": questions}
                    st.session_state.time_limit_seconds = num_questions * per_q_seconds
                    st.session_state.quiz_started = True
                    st.session_state.quiz_finished = False
                    st.session_state.current_question = 0
                    st.session_state.user_answers = [None] * len(questions)
                    st.session_state.start_time = datetime.now()
                    st.session_state.quiz_subject = subject
                    st.session_state.quiz_topic = topic
                    st.session_state.quiz_difficulty = difficulty
                    st.session_state.quiz_grade = grade
                    st.rerun()

            st.markdown("</div></div>", unsafe_allow_html=True)
        return

    if not st.session_state.quiz_finished:
        display_quiz()
    else:
        show_results()


def display_quiz():
    questions = safe_questions_list(st.session_state.quiz_data)
    if not questions:
        st.session_state.quiz_started = False
        st.rerun()
        return

    st.session_state.current_question = clamp(
        st.session_state.current_question, 0, len(questions) - 1
    )
    current_q = st.session_state.current_question
    question = questions[current_q]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
        <div class="card">
            <div class="card-header bg-info text-white"><i class="bi bi-mortarboard"></i> پایه</div>
            <div class="card-body text-center"><h5>{st.session_state.quiz_grade}</h5></div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="card">
            <div class="card-header bg-success text-white"><i class="bi bi-journal-bookmark"></i> درس/مبحث</div>
            <div class="card-body text-center"><h5>{st.session_state.quiz_subject} - {st.session_state.quiz_topic}</h5></div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="card">
            <div class="card-header bg-warning text-dark"><i class="bi bi-speedometer2"></i> سختی</div>
            <div class="card-body text-center"><h5>{st.session_state.quiz_difficulty}</h5></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    elapsed = (datetime.now() - st.session_state.start_time).total_seconds()
    remaining = max(0, st.session_state.time_limit_seconds - int(elapsed))
    if remaining == 0:
        st.warning("زمان آزمون به پایان رسید.")
        st.session_state.quiz_finished = True
        st.rerun()
        return

    minutes, seconds = divmod(remaining, 60)
    progress_ratio = min(1.0, max(0.0, elapsed / max(1, st.session_state.time_limit_seconds)))

    st.markdown(
        f"""
    <div class="timer-container">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <i class="bi bi-clock"></i> زمان باقیمانده:
                <span style="font-size: 1.5rem; font-weight: bold;">{int(minutes):02d}:{int(seconds):02d}</span>
            </div>
            <div>
                پیشرفت: {current_q + 1} از {len(questions)}
            </div>
        </div>
        <div class="progress mt-2" style="height: 10px;">
            <div class="progress-bar" role="progressbar"
                 style="width: {progress_ratio * 100:.1f}%;" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
    <div class="card">
        <div class="card-header bg-primary text-white">
            <div class="d-flex align-items-center">
                <div class="question-number">{current_q + 1}</div>
                سوال
            </div>
        </div>
        <div class="card-body">
            <h5 class="card-title">{question["question_text"]}</h5>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    option_labels = ["الف", "ب", "ج", "د"]
    for i, option in enumerate(question["options"]):
        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown(f'<div class="option-label">{option_labels[i]}</div>', unsafe_allow_html=True)
        with col2:
            if st.button(option, key=f"option_{current_q}_{i}", use_container_width=True):
                st.session_state.user_answers[current_q] = i
                if current_q < len(questions) - 1:
                    st.session_state.current_question += 1
                st.rerun()

    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 2])
    with col_a:
        if st.button("⏪ قبلی", use_container_width=True) and current_q > 0:
            st.session_state.current_question -= 1
            st.rerun()
    with col_c:
        if st.button("بعدی ⏩", use_container_width=True) and current_q < len(questions) - 1:
            st.session_state.current_question += 1
            st.rerun()
    with col_d:
        if st.button("✅ پایان آزمون", type="primary", use_container_width=True):
            st.session_state.quiz_finished = True
            st.rerun()


def show_results():
    questions = safe_questions_list(st.session_state.quiz_data)
    user_answers = st.session_state.user_answers
    correct_count = 0
    for i, q in enumerate(questions):
        ans = user_answers[i] if i < len(user_answers) else None
        if ans is not None and 0 <= ans < len(q["options"]) and ans == q["correct_option_index"]:
            correct_count += 1

    total = max(1, len(questions))
    score = (correct_count / total) * 100.0

    st.markdown(
        f"""
    <div class="card result-card">
        <div class="card-header bg-primary text-white text-center">
            <h4><i class="bi bi-trophy"></i> نتایج آزمون</h4>
        </div>
        <div class="card-body text-center">
            <h2 class="{'text-success' if score >= 70 else 'text-danger'}">نمره شما: {score:.1f}%</h2>
            <div class="d-flex justify-content-center mt-4">
                <div class="mx-3">
                    <div class="bg-success text-white p-3 rounded-circle" style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                        <h4>{correct_count}</h4>
                    </div>
                    <p class="mt-2">پاسخ صحیح</p>
                </div>
                <div class="mx-3">
                    <div class="bg-danger text-white p-3 rounded-circle" style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                        <h4>{total - correct_count}</h4>
                    </div>
                    <p class="mt-2">پاسخ نادرست</p>
                </div>
                <div class="mx-3">
                    <div class="bg-info text-white p-3 rounded-circle" style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                        <h4>{total}</h4>
                    </div>
                    <p class="mt-2">کل سوالات</p>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="card mt-4">
        <div class="card-header bg-info text-white">
            <h5><i class="bi bi-check-circle"></i> بررسی پاسخ‌ها</h5>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    option_labels = ["الف", "ب", "ج", "د"]
    for i, q in enumerate(questions):
        user_ans = user_answers[i]
        is_correct = (user_ans == q["correct_option_index"])
        st.markdown(
            f"""
        <div class="card mt-3">
            <div class="card-header {'bg-success' if is_correct else 'bg-danger'} text-white">
                سوال {i + 1}: {q['question_text']}
            </div>
            <div class="card-body">
        """,
            unsafe_allow_html=True,
        )

        for j, opt in enumerate(q["options"]):
            style = ""
            if j == q["correct_option_index"]:
                style = "correct-answer"
            elif user_ans == j and not is_correct:
                style = "wrong-answer"

            col1, col2 = st.columns([1, 10])
            with col1:
                st.markdown(f'<div class="option-label">{option_labels[j]}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="option-btn {style}">{opt}</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="alert alert-info mt-3">
                <strong><i class="bi bi-lightbulb"></i> راه حل:</strong> {q['solution']}
            </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if st.button("📝 شروع آزمون جدید", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()
