# test_api.py
import requests
import json


def test_generate_quiz():
    url = "http://localhost:8000/api/generate-quiz/"

    payload = {
        "subject": "هوش",
        "topic": "جبر",
        "difficulty": "متوسط",
        "num_questions": 3
    }

    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": "your_csrf_token_here"  # اگر نیاز باشد
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_generate_quiz()