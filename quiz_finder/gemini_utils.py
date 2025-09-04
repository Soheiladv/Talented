# quiz_finder/gemini_utils.py
import google.generativeai as genai
import os
import json
from django.conf import settings

# **مهم:** API Key خود را به صورت امن در settings.py یا متغیرهای محیطی قرار دهید
# settings.py -> GOOGLE_API_KEY = "YOUR_API_KEY"
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')  # یا مدل دیگر
except Exception as e:
    print(f"Error configuring Gemini: {e}")
    model = None


def generate_quiz_prompt(subject, topic, difficulty, num_questions):
    """
    پرامپت اصلی را برای ارسال به Gemini می‌سازد.
    """
    prompt = f"""
شما یک متخصص طراحی سوال برای آزمون تیزهوشان پایه ششم ابتدایی در ایران هستید.
وظیفه شما تولید {num_questions} سوال چهارگزینه‌ای از درس "{subject}" و مبحث "{topic}" با سطح دشواری "{difficulty}" است.

لطفاً خروجی را **دقیقاً** در فرمت JSON و به زبان فارسی ارائه دهید. ساختار JSON باید به شکل زیر باشد:
یک آبجکت اصلی با یک کلید به نام "questions". مقدار این کلید باید یک آرایه از آبجکت‌های سوال باشد.
هر آبجکت سوال باید شامل کلیدهای زیر باشد:
- "question_text": متن کامل سوال.
- "options": یک آرایه از چهار رشته که به ترتیب گزینه‌های ۱، ۲، ۳ و ۴ هستند.
- "correct_option_index": عدد صحیح پاسخ صحیح (بین 0 تا 3).
- "solution": یک رشته حاوی راه‌حل تشریحی کامل و گام به گام سوال.

مثال برای یک سوال:
{{
  "questions": [
    {{
      "question_text": "اگر یک پنجم عددی برابر با 12 باشد، آن عدد کدام است؟",
      "options": ["50", "60", "70", "80"],
      "correct_option_index": 1,
      "solution": "برای پیدا کردن عدد، باید 12 را در 5 ضرب کنیم. 12 × 5 = 60. پس پاسخ صحیح گزینه 2 یعنی 60 است."
    }}
  ]
}}

لطفاً فقط و فقط JSON خواسته شده را بدون هیچ متن اضافی، مقدمه یا توضیحی در خروجی برگردان.
"""
    return prompt


def generate_quiz_from_gemini(subject, topic, difficulty, num_questions=5):
    """
    به Gemini متصل شده، سوالات را تولید کرده و به صورت یک دیکشنری پایتون برمی‌گرداند.
    """
    if not model:
        raise Exception("Gemini model is not configured.")

    prompt = generate_quiz_prompt(subject, topic, difficulty, num_questions)

    try:
        response = model.generate_content(prompt)
        # تمیز کردن خروجی برای استخراج JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        # پارس کردن رشته JSON به دیکشنری پایتون
        quiz_data = json.loads(json_text)

        # اعتبارسنجی اولیه ساختار JSON
        if 'questions' not in quiz_data or not isinstance(quiz_data['questions'], list):
            raise ValueError("Generated JSON does not have the correct structure.")

        return quiz_data

    except Exception as e:
        print(f"An error occurred while generating quiz from Gemini: {e}")
        # اینجا می‌توانید چند بار تلاش مجدد (retry) را هم پیاده‌سازی کنید
        return None