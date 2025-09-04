# quiz_finder/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _

class QuizRequestForm(forms.Form):
    SUBJECT_CHOICES = [
        ('ریاضی', _('ریاضی')),
        ('علوم', _('علوم')),
        ('هوش و استعداد تحلیلی', _('هوش و استعداد تحلیلی')),
    ]
    DIFFICULTY_CHOICES = [
        ('ساده', _('ساده')),
        ('متوسط', _('متوسط')),
        ('دشوار', _('دشوار')),
    ]

    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        label=_("کدام درس؟"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    topic = forms.CharField(
        label=_("چه مبحثی؟ (اختیاری)"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('مثال: کسرها، انرژی، هوش تصویری')})
    )
    num_questions = forms.IntegerField(
        label=_("چند تا سوال؟"),
        min_value=1,
        max_value=20,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        label=_("سطح سختی سوالات؟"),
        initial='متوسط',
        widget=forms.Select(attrs={'class': 'form-select'})
    )