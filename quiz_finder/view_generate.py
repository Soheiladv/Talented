# ===== IMPORTS & DEPENDENCIES =====
from django.views.generic import FormView, View
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import logging

# ===== CONFIGURATION & CONSTANTS =====
HUGGINGFACE_TIMEOUT = 20  # ثانیه
logger = logging.getLogger(__name__)

# ===== UTILITY FUNCTIONS =====
def generate_mock_quiz(subject, topic, difficulty, num_questions):
    """تولید سوالات mock در صورت مشکل مدل آنلاین"""
    return {
        "success": True,
        "quiz": {
            "questions": [
                {"question_text": "عدد ۵ + ۳ برابر است با؟",
                 "options": ["۷", "۸", "۹", "۱۰"],
                 "correct_option_index": 1,
                 "solution": "۵ + ۳ = ۸"},
                {"question_text": "رنگ آسمان در روز صاف چیست؟",
                 "options": ["سبز", "آبی", "قرمز", "زرد"],
                 "correct_option_index": 1,
                 "solution": "رنگ آسمان در روز صاف آبی است"}
            ][:num_questions]
        },
        "time_limit_seconds": 270,
        "message": f"{num_questions} سوال تولید شد"
    }

def call_huggingface_model(payload):
    """تلاش برای گرفتن quiz از مدل آنلاین"""
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    headers = {"Authorization": "Bearer YOUR_HF_TOKEN"}
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=HUGGINGFACE_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Connection to Hugging Face failed: {e}")
        return None

# ===== CORE BUSINESS LOGIC / SERVICES =====
def generate_quiz_service(subject, topic, difficulty, num_questions):
    payload = {
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "num_questions": num_questions
    }
    result = call_huggingface_model(payload)
    if result is None:
        return generate_mock_quiz(subject, topic, difficulty, num_questions)
    return result

# ===== API ROUTES / VIEWS =====
class QuizHomeView(FormView):
    template_name = "quiz_finder/gen1.html"
    success_url = reverse_lazy("generate_quiz_api")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "آزمون خود را بسازید"
        return context

@method_decorator(csrf_exempt, name="dispatch")
class GenerateQuizAPI(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            subject = data.get("subject")
            topic = data.get("topic")
            difficulty = data.get("difficulty")
            num_questions = int(data.get("num_questions", 3))
            quiz = generate_quiz_service(subject, topic, difficulty, num_questions)
            return JsonResponse(quiz)
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return JsonResponse({"success": False, "error": "مشکلی در سرور رخ داده است."})
