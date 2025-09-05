# utils/hf_quiz.py
import logging
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

# Mock fallback quiz
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


def generate_quiz(subject: str, topic: str, difficulty: str, num_questions: int = 5, hf_token: str = None):
    """
    تولید سوال چندگزینه‌ای با استفاده از مدل gated Hugging Face.
    در صورت عدم موفقیت، از Mock Quiz استفاده می‌کند.
    """
    if not hf_token:
        logger.warning("Hugging Face API token not provided. Using mock quiz.")
        return MOCK_QUIZ

    prompt = f"""Generate {num_questions} multiple-choice questions in Persian.
Subject: "{subject}"
Topic: "{topic}"
Difficulty Level: "{difficulty}"

The output must be only a valid JSON object. Do not include any text or markdown.
JSON structure: {{"questions": [{{"question_text": "...", "options": ["...", "...", "...", "..."], "correct_option_index": 0, "solution": "..."}}]}}
"""

    try:
        client = InferenceClient(token=hf_token)
        output = client.text_generation(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            inputs=prompt
        )

        # متن خروجی مدل
        generated_text = output[0].get("generated_text", "")

        # استخراج JSON از متن
        import json
        json_start = generated_text.find("{")
        json_end = generated_text.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            logger.warning("No JSON found in model output. Using mock quiz.")
            return MOCK_QUIZ

        quiz_data = json.loads(generated_text[json_start:json_end])
        if 'questions' not in quiz_data or not isinstance(quiz_data['questions'], list):
            logger.warning("JSON missing 'questions'. Using mock quiz.")
            return MOCK_QUIZ

        return quiz_data

    except Exception as e:
        logger.warning(f"Failed to generate quiz from Hugging Face model: {e}")
        return MOCK_QUIZ
