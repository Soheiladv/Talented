# quiz_finder/models.py
from django.db import models
from django.conf import settings


class GeneratedQuiz(models.Model):
    """یک آزمون کامل که توسط Gemini تولید و در دیتابیس ذخیره شده است."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_quizzes')
    subject = models.CharField(max_length=50, verbose_name="درس")
    topic = models.CharField(max_length=200, verbose_name="مبحث")
    difficulty = models.CharField(max_length=50, verbose_name="سطح دشواری")

    # داده‌های آزمون به صورت JSON ذخیره می‌شوند
    quiz_data = models.JSONField(verbose_name="داده‌های آزمون (سوالات، گزینه‌ها، پاسخ‌ها)")

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"آزمون {self.subject} ({self.topic}) برای کاربر {self.user.username}"

# مدل UserAnswer می‌تواند مانند قبل باشد، با این تفاوت که به جای Question به GeneratedQuiz و یک شناسه سوال (مثلاً index) اشاره کند.