import openai
import streamlit as st
import requests
import json
import random
import time
from datetime import datetime

from Scripts.wmitest import settings
from openai.lib._parsing._responses import parse_response

from quiz_finder.view_generate import call_huggingface_model, generate_mock_quiz

# تنظیمات صفحه
st.set_page_config(
    page_title="سازنده سوالات تیزهوشان",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# اضافه کردن Bootstrap
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<style>
    .main-header {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .card {
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s;
        margin-bottom: 1.5rem;
        border: none;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .card-header {
        border-radius: 15px 15px 0 0 !important;
        font-weight: 600;
    }
    .btn-primary {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
    }
    .btn-primary:hover {
        background: linear-gradient(135deg, #5a0db9 0%, #1c65e0 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .option-btn {
        text-align: right;
        direction: rtl;
        margin: 0.5rem 0;
        transition: all 0.3s;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
    }
    .option-btn:hover {
        background-color: #f8f9fa;
        border-color: #6a11cb;
    }
    .correct-answer {
        background-color: #d4edda !important;
        border-color: #28a745 !important;
        color: #155724;
    }
    .wrong-answer {
        background-color: #f8d7da !important;
        border-color: #dc3545 !important;
        color: #721c24;
    }
    .progress-bar {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .result-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 5px solid #6a11cb;
    }
    .subject-badge {
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.2rem;
    }
    .timer-container {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    .question-number {
        background: #6a11cb;
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# داده‌های نمونه برای زمانی که API در دسترس نیست
SAMPLE_QUESTIONS = {
    "ریاضی": {
        "آسان": [
            {
                "question_text": "حاصل جمع ۱۵ و ۲۳ چیست؟",
                "options": ["۳۸", "۳۷", "۳۹", "۴۰"],
                "correct_option_index": 0,
                "solution": "۱۵ + ۲۳ = ۳۸"
            },
            {
                "question_text": "مساحت مربعی با ضلع ۵ سانتیمتر چقدر است؟",
                "options": ["۲۰ سانتیمتر مربع", "۲۵ سانتیمتر مربع", "۱۰ سانتیمتر مربع", "۱۵ سانتیمتر مربع"],
                "correct_option_index": 1,
                "solution": "مساحت مربع = ضلع × ضلع = ۵ × ۵ = ۲۵"
            },
            {
                "question_text": "حاصل ضرب ۷ × ۸ چیست؟",
                "options": ["۵۴", "۵۶", "۵۸", "۶۰"],
                "correct_option_index": 1,
                "solution": "۷ × ۸ = ۵۶"
            }
        ],
        "متوسط": [
            {
                "question_text": "اگر ۲x + ۵ = ۱۵ باشد، مقدار x چقدر است؟",
                "options": ["۵", "۱۰", "۷", "۸"],
                "correct_option_index": 0,
                "solution": "۲x = ۱۵ - ۵ => ۲x = ۱۰ => x = ۵"
            },
            {
                "question_text": "حجم مکعبی با ضلع ۳ سانتیمتر چقدر است؟",
                "options": ["۹ سانتیمتر مکعب", "۱۸ سانتیمتر مکعب", "۲۷ سانتیمتر مکعب", "۳۶ سانتیمتر مکعب"],
                "correct_option_index": 2,
                "solution": "حجم مکعب = ضلع × ضلع × ضلع = ۳ × ۳ × ۳ = ۲۷"
            }
        ],
        "سخت": [
            {
                "question_text": "در مثلث قائم‌الزاویه، وتر ۱۰ سانتیمتر و یکی از اضلاع ۶ سانتیمتر است. ضلع دیگر چقدر است؟",
                "options": ["۸ سانتیمتر", "۷ سانتیمتر", "۹ سانتیمتر", "۱۰ سانتیمتر"],
                "correct_option_index": 0,
                "solution": "طبق قضیه فیثاغورس: a² + b² = c² => ۶² + b² = ۱۰² => ۳۶ + b² = ۱۰۰ => b² = ۶۴ => b = ۸"
            },
            {
                "question_text": "اگر مجموع سه عدد زوج متوالی ۷۲ باشد، بزرگترین عدد کدام است؟",
                "options": ["۲۲", "۲۴", "۲۶", "۲۸"],
                "correct_option_index": 2,
                "solution": "اعداد را x, x+۲, x+۴ در نظر می‌گیریم: x + (x+۲) + (x+۴) = ۷۲ => ۳x + ۶ = ۷۲ => ۳x = ۶۶ => x = ۲۲. بزرگترین عدد: ۲۲ + ۴ = ۲۶"
            }
        ]
    },
    "علوم": {
        "آسان": [
            {
                "question_text": "کدام گزینه از منابع انرژی تجدیدپذیر است؟",
                "options": ["نفت", "زغال سنگ", "انرژی خورشیدی", "گاز طبیعی"],
                "correct_option_index": 2,
                "solution": "انرژی خورشیدی یک منبع انرژی تجدیدپذیر است."
            },
            {
                "question_text": "کدام سیاره به ستاره سرخ معروف است؟",
                "options": ["مریخ", "زهره", "مشتری", "زمین"],
                "correct_option_index": 0,
                "solution": "سیاره مریخ به دلیل وجود اکسید آهن در سطح آن به ستاره سرخ معروف است."
            }
        ],
        "متوسط": [
            {
                "question_text": "کدام سلول در سیستم ایمنی بدن مسئول تولید پادتن است؟",
                "options": ["گلبول قرمز", "پلاکت", "لنفوسیت B", "لنفوسیت T"],
                "correct_option_index": 2,
                "solution": "لنفوسیت‌های B مسئول تولید پادتن در سیستم ایمنی بدن هستند."
            },
            {
                "question_text": "کدام گزینه از ویژگی‌های فلزات نیست؟",
                "options": ["رسانایی الکتریکی", "رسانایی گرمایی", "شکنندگی", "چکش‌خواری"],
                "correct_option_index": 2,
                "solution": "شکنندگی از ویژگی‌های غیرفلزات است، نه فلزات."
            }
        ],
        "سخت": [
            {
                "question_text": "در کدام مرحله از تقسیم میوز، تبادل مواد ژنتیکی بین کروموزوم‌های همولوگ رخ می‌دهد؟",
                "options": ["پروفاز I", "متافاز I", "آنافاز I", "تلوفاز I"],
                "correct_option_index": 0,
                "solution": "در پروفاز I میوز، کروموزوم‌های همولوگ جفت شده و تبادل مواد ژنتیکی (کراسینگ اور) انجام می‌شود."
            },
            {
                "question_text": "کدام عنصر در گروه ۱۸ جدول تناوبی قرار ندارد؟",
                "options": ["نئون", "آرگون", "کلر", "هلیوم"],
                "correct_option_index": 2,
                "solution": "کلر در گروه ۱۷ (هالوژن‌ها) قرار دارد، نه گروه ۱۸ (گازهای نجیب)."
            }
        ]
    },
    "هوش": {
        "آسان": [
            {
                "question_text": "عدد بعدی در دنباله ۲, ۴, ۶, ۸, ... چیست؟",
                "options": ["۱۰", "۱۲", "۱۴", "۱۶"],
                "correct_option_index": 0,
                "solution": "این دنباله اعداد زوج است و عدد بعدی ۱۰ می‌باشد."
            },
            {
                "question_text": "کدام گزینه با بقیه متفاوت است؟",
                "options": ["سیب", "موز", "پرتقال", "هویج"],
                "correct_option_index": 3,
                "solution": "هویج جزو سبزیجات است، در حالی که بقیه میوه هستند."
            }
        ],
        "متوسط": [
            {
                "question_text": "اگر همه «گل‌ها» «گیاه» باشند و بعضی «گیاهان» «سبز» باشند، کدام گزینه قطعاً درست است؟",
                "options": [
                    "همه گل‌ها سبز هستند",
                    "بعضی گل‌ها سبز هستند",
                    "هیچ گلی سبز نیست",
                    "بعضی گیاهان گل نیستند"
                ],
                "correct_option_index": 3,
                "solution": "از آنجایی که همه گل‌ها گیاه هستند، ولی بعضی گیاهان سبز هستند، قطعاً بعضی گیاهان گل نیستند."
            },
            {
                "question_text": "اگر A = 1, B = 2, C = 3 باشد، حاصل جمع ارزش حروف کلمه CAT چیست؟",
                "options": ["۲۴", "۲۰", "۱۸", "۱۵"],
                "correct_option_index": 0,
                "solution": "C=3, A=1, T=20 → 3+1+20=24"
            }
        ],
        "سخت": [
            {
                "question_text": "اگر ۵ ماشین ۵ دقیقه وقت لازم داشته باشند تا ۵ دستگاه تولید کنند، چند دقیقه طول می‌کشد تا ۱۰۰ ماشین ۱۰۰ دستگاه تولید کنند؟",
                "options": ["۵ دقیقه", "۱۰ دقیقه", "۲۰ دقیقه", "۱۰۰ دقیقه"],
                "correct_option_index": 0,
                "solution": "هر ماشین به ۵ دقیقه زمان برای تولید یک دستگاه نیاز دارد. بنابراین ۱۰۰ ماشین نیز برای تولید ۱۰۰ دستگاه به ۵ دقیقه زمان نیاز دارند."
            },
            {
                "question_text": "کدام عدد جایگزین علامت سؤال باید شود؟\n۲, ۳, ۵, ۷, ۱۱, ۱۳, ?",
                "options": ["۱۵", "۱۷", "۱۹", "۲۱"],
                "correct_option_index": 1,
                "solution": "این دنباله اعداد اول است و عدد اول بعد از ۱۳، عدد ۱۷ می‌باشد."
            }
        ]
    }
}


def generate_quiz_service(subject, topic, difficulty, num_questions):
    """
    سرویس تولید آزمون با هوش مصنوعی با fallback به سوالات نمونه
    """
    payload = {
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "num_questions": num_questions
    }

    # تماس با مدل Hugging Face
    # result = call_huggingface_model(payload)
    prompt = f"برای درس {subject} و مبحث {topic} سطح {difficulty}، {num_questions} سوال با چهار گزینه و جواب درست بساز."
    response = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
    questions = parse_response(response)
    if questions is None:
        return generate_mock_quiz(subject, topic, difficulty, num_questions)
    return {"success": True, "quiz": {"questions": questions}, "time_limit_seconds": num_questions * 90}

    # if result is None:
    #     # اگر مدل در دسترس نبود، از سوالات نمونه استفاده کن
    #     return generate_mock_quiz(subject, topic, difficulty, num_questions)

    # return result

def call_huggingface_model(payload):
    """
    فراخوانی API Hugging Face برای تولید سوال
    """
    import requests
    import json

    url = "https://api-inference.huggingface.co/models/your-model-name"
    hf_token = getattr(settings, "HUGGINGFACE_API_TOKEN", None)

    headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        # parse data to match your quiz format
        return data
    except Exception as e:
        print(f"Error calling Hugging Face model: {e}")
        return None


# prompt = f"برای درس {subject} و مبحث {topic} سطح {difficulty}، {num_questions} سوال با چهار گزینه و جواب درست بساز."
# response = openai.ChatCompletion.create(model="gpt-4", messages=[{"role":"user","content":prompt}])
# questions = parse_response(response)

def generate_quiz_api(subject, topic, difficulty, num_questions):
    """تابع برای تولید سوالات از طریق API"""
    try:
        # شبیه‌سازی تاخیر شبکه
        time.sleep(1.5)

        # انتخاب سوالات از داده‌های نمونه
        questions = []
        if subject in SAMPLE_QUESTIONS and difficulty in SAMPLE_QUESTIONS[subject]:
            available_questions = SAMPLE_QUESTIONS[subject][difficulty]
            # اگر تعداد سوالات درخواستی بیشتر از نمونه‌ها باشد، بعضی را تکرار می‌کنیم
            for i in range(num_questions):
                questions.append(available_questions[i % len(available_questions)])

        return {
            "success": True,
            "quiz": {"questions": questions},
            "time_limit_seconds": num_questions * 90
        }

    except Exception as e:
        st.error(f"خطا در ارتباط با سرور: {str(e)}")
        return None


def main():
    # هدر اصلی با Bootstrap
    st.markdown("""
    <div class="main-header text-center">
        <h1><i class="bi bi-lightbulb"></i> سازنده سوالات تیزهوشان</h1>
        <p class="lead">پلتفرم هوشمند تولید سوالات استاندارد برای مدارس تیزهوشان</p>
    </div>
    """, unsafe_allow_html=True)

    # اگر آزمونی در حال برگزاری نیست، فرم تنظیمات را نشان بده
    if 'quiz_started' not in st.session_state or not st.session_state.quiz_started:
        with st.sidebar:
            st.markdown("""
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <i class="bi bi-gear"></i> تنظیمات آزمون
                </div>
                <div class="card-body">
            """, unsafe_allow_html=True)

            # انتخاب پایه تحصیلی
            grade = st.selectbox(
                "پایه تحصیلی",
                ["سوم ابتدایی", "چهارم ابتدایی", "پنجم ابتدایی", "ششم ابتدایی",
                 "هفتم", "هشتم", "نهم"]
            )

            # انتخاب درس
            subject = st.selectbox(
                "درس",
                ["ریاضی", "علوم", "هوش"]
            )

            # انتخاب مبحث (بر اساس درس انتخاب شده)
            if subject == "ریاضی":
                topics = ["جبر", "هندسه", "احتمال", "آمار", "عدد و عملیات"]
            elif subject == "علوم":
                topics = ["فیزیک", "شیمی", "زیست‌شناسی", "زمین‌شناسی", "نجوم"]
            else:  # هوش
                topics = ["استدلال منطقی", "الگویابی", "حل مسئله", "تصویری", "کلامی"]

            topic = st.selectbox("مبحث", topics)

            # انتخاب سطح سختی
            difficulty = st.select_slider(
                "سطح سختی",
                options=["آسان", "متوسط", "سخت"]
            )

            # تعداد سوالات
            num_questions = st.slider(
                "تعداد سوالات",
                min_value=3,
                max_value=20,
                value=5
            )

            # دکمه شروع آزمون
            if st.button("شروع آزمون", type="primary"):
                with st.spinner("در حال تولید سوالات..."):
                    result = generate_quiz_api(subject, topic, difficulty, num_questions)

                    if result and result.get("success"):
                        st.session_state.quiz_data = result["quiz"]
                        st.session_state.time_limit = result["time_limit_seconds"]
                        st.session_state.quiz_started = True
                        st.session_state.current_question = 0
                        st.session_state.user_answers = [None] * num_questions
                        st.session_state.start_time = datetime.now()
                        st.session_state.quiz_subject = subject
                        st.session_state.quiz_topic = topic
                        st.session_state.quiz_difficulty = difficulty
                        st.session_state.quiz_grade = grade
                        st.rerun()
                    else:
                        st.error("خطا در تولید سوالات. لطفاً دوباره تلاش کنید.")

            st.markdown("</div></div>", unsafe_allow_html=True)

    else:
        # نمایش سوالات آزمون
        display_quiz()

        # دکمه پایان آزمون
        if st.button("پایان آزمون و نمایش نتیجه", type="primary"):
            st.session_state.quiz_finished = True
            st.rerun()


def display_quiz():
    # نمایش اطلاعات آزمون
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-header bg-info text-white">
                <i class="bi bi-mortarboard"></i> پایه تحصیلی
            </div>
            <div class="card-body text-center">
                <h5>{st.session_state.quiz_grade}</h5>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <div class="card-header bg-success text-white">
                <i class="bi bi-journal-bookmark"></i> درس و مبحث
            </div>
            <div class="card-body text-center">
                <h5>{st.session_state.quiz_subject} - {st.session_state.quiz_topic}</h5>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <i class="bi bi-speedometer2"></i> سطح سختی
            </div>
            <div class="card-body text-center">
                <h5>{st.session_state.quiz_difficulty}</h5>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # نمایش تایمر
    elapsed_time = (datetime.now() - st.session_state.start_time).seconds
    remaining_time = max(0, st.session_state.time_limit - elapsed_time)
    minutes, seconds = divmod(remaining_time, 60)

    st.markdown(f"""
    <div class="timer-container">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <i class="bi bi-clock"></i> زمان باقیمانده: 
                <span style="font-size: 1.5rem; font-weight: bold;">
                    {minutes:02d}:{seconds:02d}
                </span>
            </div>
            <div>
                پیشرفت: {st.session_state.current_question + 1} از {len(st.session_state.quiz_data['questions'])}
            </div>
        </div>
        <div class="progress mt-2" style="height: 10px;">
            <div class="progress-bar" role="progressbar" 
                 style="width: {(elapsed_time / st.session_state.time_limit) * 100}%;" 
                 aria-valuenow="{(elapsed_time / st.session_state.time_limit) * 100}" 
                 aria-valuemin="0" aria-valuemax="100"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # نمایش سوال جاری
    questions = st.session_state.quiz_data["questions"]
    current_q = st.session_state.current_question
    question = questions[current_q]

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

    # نمایش گزینه‌ها
    for i, option in enumerate(question["options"]):
        if st.button(option, key=f"option_{i}", use_container_width=True):
            st.session_state.user_answers[current_q] = i
            if current_q < len(questions) - 1:
                st.session_state.current_question += 1
            st.rerun()

    # دکمه‌های navigation
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("⏪ قبلی", use_container_width=True) and current_q > 0:
            st.session_state.current_question -= 1
            st.rerun()
    with col3:
        if st.button("بعدی ⏩", use_container_width=True) and current_q < len(questions) - 1:
            st.session_state.current_question += 1
            st.rerun()
    with col4:
        if st.button("✅ پایان آزمون", type="primary", use_container_width=True):
            st.session_state.quiz_finished = True
            st.rerun()


def show_results():
    # محاسبه نتایج
    questions = st.session_state.quiz_data["questions"]
    user_answers = st.session_state.user_answers
    correct_count = 0

    for i, question in enumerate(questions):
        if user_answers[i] == question["correct_option_index"]:
            correct_count += 1

    score = (correct_count / len(questions)) * 100

    # نمایش نتایج
    st.markdown(f"""
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
                        <h4>{len(questions) - correct_count}</h4>
                    </div>
                    <p class="mt-2">پاسخ نادرست</p>
                </div>
                <div class="mx-3">
                    <div class="bg-info text-white p-3 rounded-circle" style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                        <h4>{len(questions)}</h4>
                    </div>
                    <p class="mt-2">کل سوالات</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # نمایش پاسخ‌های صحیح
    st.markdown("""
    <div class="card mt-4">
        <div class="card-header bg-info text-white">
            <h5><i class="bi bi-check-circle"></i> بررسی پاسخ‌ها</h5>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for i, question in enumerate(questions):
        user_answer = user_answers[i]
        is_correct = user_answer == question["correct_option_index"]

        st.markdown(f"""
        <div class="card mt-3">
            <div class="card-header {'bg-success' if is_correct else 'bg-danger'} text-white">
                سوال {i + 1}: {question['question_text']}
                <span class="badge bg-light text-dark float-left">
                    {['آسان', 'متوسط', 'سخت'][['آسان', 'متوسط', 'سخت'].index(st.session_state.quiz_difficulty)]}
                </span>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)

        for j, option in enumerate(question["options"]):
            style = ""
            if j == question["correct_option_index"]:
                style = "correct-answer"
            elif j == user_answer and not is_correct:
                style = "wrong-answer"

            st.markdown(f'<div class="option-btn {style}">{option}</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="alert alert-info mt-3">
            <strong><i class="bi bi-lightbulb"></i> راه حل:</strong> {question['solution']}
        </div>
        </div></div>
        """, unsafe_allow_html=True)

    # دکمه شروع آزمون جدید
    if st.button("📝 شروع آزمون جدید", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    if 'quiz_finished' in st.session_state and st.session_state.quiz_finished:
        show_results()
    else:
        main()