import requests
import json
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

# 🔑 توکن API Hugging Face
API_TOKEN = getattr(settings, "HUGGINGFACE_API_TOKEN", None)

# 📌 مدل‌های تایید شده

HF_MODELS = [
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
    "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
]

# ❌ Mock fallback در صورت عدم اتصال
MOCK_QUIZ = {
    "questions": [
        {
            "question_text": "عدد ۵ + ۳ برابر است با؟",
            "options": ["۷", "۸", "۹", "۱۰"],
            "correct_option_index": 1,
            "solution": "۵ + ۳ = ۸"
        },
        {
            "question_text": "رنگ آسمان در روز صاف چیست؟",
            "options": ["سبز", "آبی", "قرمز", "زرد"],
            "correct_option_index": 1,
            "solution": "رنگ آسمان در روز صاف آبی است"
        }
    ]
}

# ❌ جلوگیری از استفاده از پروکسی سیستم
os.environ['NO_PROXY'] = 'api-inference.huggingface.co'


def generate_quiz_from_huggingface(subject, topic, difficulty, num_questions=5):
    """
    تولید سوال چندگزینه‌ای با استفاده از مدل‌های Hugging Face.
    در صورت عدم اتصال، از Mock fallback استفاده می‌کند.
    """
    if not API_TOKEN:
        logger.warning("Hugging Face API Token not found. Using mock quiz.")
        return MOCK_QUIZ

    prompt = f"""Generate {num_questions} multiple-choice questions in Persian.
Subject: "{subject}"
Topic: "{topic}"
Difficulty Level: "{difficulty}"

The output must be only a valid JSON object. Do not include any text, introductions, or markdown.
The JSON structure must be: {{"questions": [{{"question_text": "...", "options": ["...", "...", "...", "..."], "correct_option_index": 0, "solution": "..."}}]}}

JSON object:
"""

    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 2048,
            "return_full_text": False,
            "temperature": 0.7,
        }
    }

    for model_url in HF_MODELS:
        try:
            response = requests.post(
                model_url,
                headers=headers,
                json=payload,
                timeout=45,
                proxies={"http": None, "https": None}  # عدم استفاده از پروکسی
            )
            response.raise_for_status()
            result = response.json()
            result_text = result[0].get("generated_text", "")

            # پیدا کردن JSON در متن خروجی
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                logger.warning(f"No JSON found in model response for {model_url}")
                continue

            json_string = result_text[json_start:json_end]
            quiz_data = json.loads(json_string)

            if 'questions' not in quiz_data or not isinstance(quiz_data['questions'], list):
                logger.warning(f"JSON missing 'questions' for {model_url}")
                continue

            logger.info(f"Successfully generated {len(quiz_data['questions'])} questions using {model_url}")
            return quiz_data

        except requests.RequestException as e:
            logger.warning(f"Connection failed for model {model_url}: {e}")

        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error parsing response from {model_url}: {e}")

    logger.info("Falling back to mock quiz data.")
    return MOCK_QUIZ

import os
# import json
# import logging
# import requests
# from django.conf import settings
# import urllib3
#
# # غیرفعال کردن هشدارهای SSL
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#
# logger = logging.getLogger(__name__)
#
# # توکن Hugging Face
# API_TOKEN = getattr(settings, "HUGGINGFACE_API_TOKEN", None)
# if not API_TOKEN:
#     logger.warning("Hugging Face API Token not found in settings. Using mock data.")
#
# # غیرفعال کردن پروکسی برای Hugging Face
# os.environ['NO_PROXY'] = ','.join(MODELS)
#
#
# def generate_quiz_from_huggingface(subject, topic, difficulty, num_questions=5):
#     """
#     تولید سوالات چندگزینه‌ای با Hugging Face یا fallback به mock داده.
#     """
#
#     prompt = f"""Generate {num_questions} multiple-choice questions in Persian.
# Subject: "{subject}"
# Topic: "{topic}"
# Difficulty Level: "{difficulty}"
#
# Output must be only a valid JSON object.
# JSON structure: {{"questions": [{{"question_text": "...", "options": ["...", "...", "...", "..."], "correct_option_index": 0, "solution": "..."}}]}}
#
# JSON object:
# """
#
#     headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
#
#     for model_url in MODELS:
#         if not API_TOKEN:
#             continue  # skip actual requests if no token
#
#         try:
#             response = requests.post(
#                 model_url,
#                 headers=headers,
#                 json={"inputs": prompt, "parameters": {"max_new_tokens": 2048, "return_full_text": False, "temperature": 0.7}},
#                 timeout=30,
#                 proxies={"http": None, "https": None}
#             )
#             response.raise_for_status()
#             result = response.json()
#             result_text = result[0].get("generated_text", "")
#
#             json_start = result_text.find("{")
#             json_end = result_text.rfind("}") + 1
#             if json_start == -1 or json_end == 0:
#                 continue
#
#             json_string = result_text[json_start:json_end]
#             quiz_data = json.loads(json_string)
#
#             if 'questions' in quiz_data and isinstance(quiz_data['questions'], list):
#                 logger.info(f"Generated {len(quiz_data['questions'])} questions from Hugging Face ({model_url}).")
#                 return quiz_data
#
#         except requests.exceptions.RequestException as e:
#             logger.warning(f"Connection failed for model {model_url}: {e}")
#
#         except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
#             logger.warning(f"Failed parsing Hugging Face response from {model_url}: {e}")
#
#     # ⚠️ fallback به داده mock اگر همه درخواست‌ها شکست خورد
#     logger.info("Falling back to mock quiz data.")
#     return {
#         "questions": [
#             {
#                 "question_text": f"نمونه سوال {i+1} در درس {subject} موضوع {topic}",
#                 "options": ["گزینه 1", "گزینه 2", "گزینه 3", "گزینه 4"],
#                 "correct_option_index": 0,
#                 "solution": "این یک پاسخ نمونه است."
#             } for i in range(num_questions)
#         ]
#     }
