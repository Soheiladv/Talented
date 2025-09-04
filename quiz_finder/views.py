from django.contrib import messages
from django.shortcuts import render, get_object_or_404

# Create your views here.
# quiz_finder/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .gemini_utils import generate_quiz_from_gemini
from .huggingface_utils import generate_quiz_from_huggingface
from .models import GeneratedQuiz


@login_required
def create_quiz_page(request):
    """صفحه انتخاب پارامترهای آزمون."""
    # می‌توانید مباحث و دروس را از دیتابیس یا یک لیست ثابت بخوانید
    subjects_topics = {
        'ریاضی': ['کسرها', 'هندسه', 'اعداد اعشاری'],
        'علوم': ['انرژی', 'بدن انسان', 'مواد'],
        'هوش': ['هوش تصویری', 'هوش کلامی', 'هوش منطقی']
    }
    return render(request, 'quiz_finder/create_quiz_gemini.html', {'subjects_topics': subjects_topics})


@login_required
def start_gemini_quiz(request):
    """سوالات را از Gemini تولید، در دیتابیس ذخیره و آزمون را شروع می‌کند."""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        topic = request.POST.get('topic')
        difficulty = request.POST.get('difficulty', 'متوسط')
        num_questions = int(request.POST.get('num_questions', 5))

        try:
            # ۱. تولید سوالات از Gemini
            quiz_data = generate_quiz_from_huggingface(subject, topic, difficulty, num_questions)
            quiz_data = generate_quiz_from_huggingface(subject, topic, difficulty, num_questions)

            if not quiz_data:
                # اگر تولید سوال ناموفق بود
                messages.error(request, "خطا در تولید سوالات. لطفاً دوباره تلاش کنید.")
                return redirect('create_quiz_page')

            # ۲. ذخیره آزمون تولید شده در دیتابیس
            new_quiz = GeneratedQuiz.objects.create(
                user=request.user,
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                quiz_data=quiz_data  # ذخیره کل JSON
            )

            # ۳. هدایت به صفحه آزمون
            return redirect('take_gemini_quiz', quiz_id=new_quiz.id)

        except Exception as e:
            messages.error(request, f"خطای سیستمی: {e}")
            return redirect('create_quiz_page')

    return redirect('create_quiz_page')


@login_required
def take_gemini_quiz(request, quiz_id):
    """صفحه برگزاری آزمون."""
    quiz = get_object_or_404(GeneratedQuiz, pk=quiz_id, user=request.user)
    if quiz.is_completed:
        return redirect('gemini_quiz_result', quiz_id=quiz.id)

    # زمان آزمون (مثلا ۱ دقیقه برای هر سوال)
    time_limit_minutes = len(quiz.quiz_data.get('questions', [])) * 1

    context = {
        'quiz': quiz,
        'time_limit_minutes': time_limit_minutes
    }
    return render(request, 'quiz_finder/take_quiz.html', context)


@login_required
def submit_gemini_quiz(request, quiz_id):
    """تصحیح و ذخیره نتایج آزمون."""
    quiz = get_object_or_404(GeneratedQuiz, pk=quiz_id, user=request.user)
    if quiz.is_completed:
        return redirect('gemini_quiz_result', quiz_id=quiz.id)

    if request.method == 'POST':
        questions = quiz.quiz_data.get('questions', [])
        correct_answers = 0
        wrong_answers = 0
        user_answers_data = []  # برای ذخیره پاسخ‌های کاربر

        for index, question_data in enumerate(questions):
            selected_option_str = request.POST.get(f'question_{index}')
            user_choice_index = int(selected_option_str) if selected_option_str else -1
            is_correct = (user_choice_index == question_data['correct_option_index'])

            if user_choice_index != -1:
                if is_correct:
                    correct_answers += 1
                else:
                    wrong_answers += 1

            user_answers_data.append({
                'question_text': question_data['question_text'],
                'options': question_data['options'],
                'correct_option_index': question_data['correct_option_index'],
                'solution': question_data['solution'],
                'user_choice_index': user_choice_index,
                'is_correct': is_correct if user_choice_index != -1 else None
            })

        # محاسبه نمره
        total_questions = len(questions)
        raw_score = (correct_answers * 3) - wrong_answers
        max_score = total_questions * 3
        score_percentage = (raw_score / max_score) * 100 if max_score > 0 else 0

        # آپدیت آزمون در دیتابیس
        quiz.quiz_data['user_answers'] = user_answers_data  # ذخیره پاسخنامه در JSON
        quiz.score = round(score_percentage, 2)
        quiz.is_completed = True
        quiz.completed_at = timezone.now()
        quiz.save()

        return redirect('gemini_quiz_result', quiz_id=quiz.id)

    return redirect('take_gemini_quiz', quiz_id=quiz.id)


@login_required
def gemini_quiz_result(request, quiz_id):
    """نمایش کارنامه آزمون."""
    quiz = get_object_or_404(GeneratedQuiz, pk=quiz_id, user=request.user)
    if not quiz.is_completed:
        return redirect('take_gemini_quiz', quiz_id=quiz.id)

    return render(request, 'quiz_finder/quiz_result_gemini.html', {'quiz': quiz})

# =====
# quiz_finder/views.py
from django.shortcuts import render
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
import json

from .forms import QuizRequestForm
from .gemini_utils import generate_quiz_from_gemini # فایلی که در پاسخ قبلی ساختیم

class QuizHomeView(FormView):
    template_name = 'quiz_finder/home.html'
    form_class = QuizRequestForm
    success_url = reverse_lazy('take_quiz') # به این آدرس نمی‌رویم، چون با AJAX کار می‌کنیم

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'آزمون خود را بسازید'
        return context

@require_POST
def generate_quiz_api(request):
    """
    یک API View که پارامترهای آزمون را با POST می‌گیرد،
    سوالات را از Gemini تولید می‌کند و به صورت JSON برمی‌گرداند.
    """
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        topic = data.get('topic')
        num_questions = int(data.get('num_questions', 5))
        difficulty = data.get('difficulty')

        if not subject:
            return JsonResponse({'error': 'درس انتخاب نشده است.'}, status=400)

        # تولید سوالات از Gemini
        quiz_data = generate_quiz_from_huggingface(subject, topic, difficulty, num_questions)
        # quiz_data = generate_quiz_from_huggingface(subject, topic, difficulty, num_questions)

        if not quiz_data or 'questions' not in quiz_data:
            return JsonResponse({'error': 'خطا در تولید سوالات از سرویس هوش مصنوعی. لطفاً دوباره تلاش کنید.'}, status=500)

        # محاسبه زمان پیشنهادی (1.5 دقیقه برای هر سوال)
        time_limit = int(num_questions * 90) # به ثانیه

        return JsonResponse({
            'success': True,
            'quiz': quiz_data,
            'time_limit_seconds': time_limit
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'درخواست نامعتبر است.'}, status=400)
    except Exception as e:
        # لاگ کردن خطا برای دیباگ
        print(f"Error in generate_quiz_api: {e}")
        return JsonResponse({'error': 'خطای داخلی سرور رخ داده است.'}, status=500)

class TakeQuizView(TemplateView):
    """این ویو فقط تمپلیت خالی آزمون را رندر می‌کند. بقیه کارها با JS است."""
    template_name = 'quiz_finder/take_quiz.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'شروع آزمون'
        context['csrf_token'] = get_token(self.request) # برای ارسال در AJAX
        return context