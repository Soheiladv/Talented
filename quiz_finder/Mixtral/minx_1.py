# ===== وارد کردن کتابخانه‌های لازم =====
import os
import re
import json
import requests
import streamlit as st
from dotenv import load_dotenv

# ===== تنظیمات و مقادیر ثابت =====
# تنظیمات اولیه صفحه Streamlit
st.set_page_config(
    page_title="آزمون ساز هوشمند",
    page_icon="🧠",
    layout="wide",
)

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HUGGINGFACE_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # مدلی که به آن دسترسی دارید

# موضوعات و مباحث پیشنهادی
SUBJECT_TOPICS = {
    "هوش و استعداد تحلیلی": ["هوش کلامی", "هوش تصویری", "استدلال منطقی"],
    "ریاضی": ["کسرها", "هندسه", "اعداد اعشاری", "تقارن و چندضلعی‌ها"],
    "علوم تجربی": ["انرژی‌ها", "بدن انسان", "مواد و تغییرات آنها", "اکوسیستم"],
}


# ===== توابع اصلی =====

def build_prompt(subject, topic, difficulty, num_questions):
    """یک پرامپت دقیق و مهندسی‌شده برای مدل Mixtral می‌سازد."""
    return f"""<s>[INST] You are an expert quiz designer for the Iranian middle school entrance exam. Your task is to generate {num_questions} multiple-choice questions in Persian.
Subject: "{subject}"
Topic: "{topic}"
Difficulty: "{difficulty}"

Your output must be **only** a valid JSON object. Do not include any extra text, introductions, or markdown formatting like ```json.
The JSON structure must be: {{"questions": [{{"question_text": "...", "options": ["...", "...", "...", "..."], "correct_option_index": 0, "solution": "..."}}]}}

Please generate the quiz now. [/INST]"""


def parse_llm_json_response(text):
    """پاسخ متنی مدل را برای پیدا کردن یک آبجکت JSON معتبر جستجو می‌کند."""
    try:
        # بهترین حالت: کل متن یک JSON است
        return json.loads(text)
    except json.JSONDecodeError:
        # حالت دوم: JSON در میان متن‌های اضافی قرار دارد
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                st.error("یک JSON ناقص در پاسخ مدل پیدا شد.")
                return None
        st.error("هیچ آبجکت JSON معتبری در پاسخ مدل یافت نشد.")
        return None


def generate_quiz_from_ai(subject, topic, difficulty, num_questions):
    """به API هوش مصنوعی متصل شده و سوالات را تولید می‌کند."""
    if not HUGGINGFACE_API_TOKEN:
        st.error("❌ توکن Hugging Face تنظیم نشده است! لطفاً فایل .env را بررسی کنید.")
        return None

    api_url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

    prompt = build_prompt(subject, topic, difficulty, num_questions)

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 2500,
            "return_full_text": False,
            "temperature": 0.7
        }
    }

    try:
        with st.spinner(f"🧠 در حال تولید {num_questions} سوال از مبحث «{topic}»..."):
            response = requests.post(api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            result_json = response.json()

            # حالت اول: خروجی لیست
            if isinstance(result_json, list) and len(result_json) > 0:
                result_text = result_json[0].get("generated_text", "")
            # حالت دوم: خروجی دیکشنری
            elif isinstance(result_json, dict):
                result_text = result_json.get("generated_text", "")
            else:
                st.error("❌ پاسخ مدل ناشناخته است.")
                st.write("Raw response:", result_json)
                return None

            quiz_data = parse_llm_json_response(result_text)

            if not quiz_data or 'questions' not in quiz_data:
                st.error("پاسخ دریافت شده از هوش مصنوعی، ساختار JSON مورد انتظار را ندارد.")
                st.write("Raw response:", result_text)
                return None

            return quiz_data

    except requests.exceptions.Timeout:
        st.error("⏳ سرور هوش مصنوعی در زمان مقرر پاسخ نداد (Timeout).")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ خطا در اتصال به Hugging Face: {e}")
        return None
    except Exception as e:
        st.error(f"🚨 خطای پیش‌بینی نشده: {e}")
        return None


# ===== رابط کاربری Streamlit =====

# مقداردهی اولیه session state برای نگهداری وضعیت آزمون
if 'page' not in st.session_state:
    st.session_state.page = 'create'
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}


# --- صفحه اصلی: ساخت آزمون ---
def render_create_page():
    st.title("📝 آزمون ساز هوشمند")
    st.markdown("درس، مبحث و سطح سختی آزمون خود را انتخاب کرده و سوالات استاندارد تولید کنید.")

    with st.form("quiz_form"):
        subject = st.selectbox("درس را انتخاب کنید:", list(SUBJECT_TOPICS.keys()))
        topic = st.selectbox("مبحث را انتخاب کنید:", SUBJECT_TOPICS[subject])
        difficulty = st.select_slider("سطح سختی:", options=["آسان", "متوسط", "سخت"], value="متوسط")
        num_questions = st.slider("تعداد سوالات:", min_value=1, max_value=10, value=3)

        submitted = st.form_submit_button("🚀 ساخت آزمون")

        if submitted:
            quiz_data = generate_quiz_from_ai(subject, topic, difficulty, num_questions)
            if quiz_data:
                st.session_state.quiz_data = quiz_data
                st.session_state.user_answers = {}  # ریست کردن پاسخ‌های قبلی
                st.session_state.page = 'take'
                st.rerun()


# --- صفحه دوم: برگزاری آزمون ---
def render_take_quiz_page():
    st.title("🧠 شروع آزمون")
    questions = st.session_state.quiz_data.get('questions', [])

    for i, q in enumerate(questions):
        st.subheader(f"سوال {i + 1}: {q['question_text']}")
        # `key` منحصر به فرد برای هر `radio` ضروری است
        answer = st.radio("گزینه‌ها:", q['options'], key=f"q_{i}", index=None)
        st.session_state.user_answers[i] = q['options'].index(answer) if answer is not None else -1
        st.divider()

    if st.button("✅ پایان و تصحیح آزمون", type="primary"):
        st.session_state.page = 'result'
        st.rerun()


# --- صفحه سوم: نمایش نتایج ---
def render_result_page():
    st.title("🏆 کارنامه آزمون")
    questions = st.session_state.quiz_data.get('questions', [])
    correct_answers = 0

    for i, q in enumerate(questions):
        user_answer_index = st.session_state.user_answers.get(i, -1)
        correct_answer_index = q['correct_option_index']

        st.subheader(f"سوال {i + 1}: {q['question_text']}")

        if user_answer_index == correct_answer_index:
            st.success(f"✅ پاسخ شما: {q['options'][user_answer_index]} (صحیح)")
            correct_answers += 1
        elif user_answer_index != -1:
            st.error(f"❌ پاسخ شما: {q['options'][user_answer_index]} (غلط)")
            st.info(f"💡 پاسخ صحیح: {q['options'][correct_answer_index]}")
        else:
            st.warning("⚪ به این سوال پاسخ نداده‌اید.")
            st.info(f"💡 پاسخ صحیح: {q['options'][correct_answer_index]}")

        with st.expander("مشاهده راه‌حل"):
            st.markdown(q['solution'])
        st.divider()

    score = (correct_answers / len(questions)) * 100
    st.header(f"نمره نهایی شما: {score:.2f} از ۱۰۰")
    st.progress(int(score))

    if st.button("📝 ساخت آزمون جدید"):
        st.session_state.page = 'create'
        st.session_state.quiz_data = None
        st.session_state.user_answers = {}
        st.rerun()


# --- مدیریت صفحات ---
if st.session_state.page == 'create':
    render_create_page()
elif st.session_state.page == 'take':
    render_take_quiz_page()
elif st.session_state.page == 'result':
    render_result_page()