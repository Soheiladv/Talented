import os

from pathlib import Path
from tempfile import template

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9457xaw-%y!tx^de(2!f0*(auzwl^5ot5vgnlq&zosraprvybm'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'quiz_finder',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tcore.urls'
# تنظیمات تمپلیت و استاتیک
TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates'),
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tcore.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGES = (('fa', 'فارسی'), ('en', 'English'))
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




GOOGLE_API_KEY = ""

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)  # مطمئن می‌شویم که پوشه لاگ حتماً وجود دارد

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # لاگرهای موجود را غیرفعال نکن

    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {funcName} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'app_debug': {  # فرمت دقیق‌تر برای دیباگ اپلیکیشن‌های خاص
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {funcName} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },

    'handlers': {
        'console': {  # هندلر برای خروجی کنسول (ترمینال)
            'level': 'DEBUG',  # در محیط توسعه، همه پیام‌های دیباگ را در کنسول نمایش بده
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_errors': {  # هندلر برای خطاهای کلی برنامه
            'level': 'ERROR',  # فقط پیام‌های خطا و بحرانی را در این فایل ذخیره کن
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'application_errors.log'),
            'maxBytes': 1024 * 1024 * 10,  # حداکثر حجم فایل 10 مگابایت
            'backupCount': 5,  # 5 فایل پشتیبان نگه دار (در مجموع 6 فایل)
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_budgets_debug': {  # هندلر اختصاصی برای دیباگ اپ 'budgets'
            'level': 'DEBUG',  # همه پیام‌های دیباگ 'budgets' را در این فایل ذخیره کن
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'budgets_debug.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 مگابایت
            'backupCount': 3,
            'formatter': 'app_debug',
            'encoding': 'utf-8',
        },
        'file_django_errors': {  # هندلر برای خطاهای داخلی جنگو (سیستم)
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'django_errors.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 3,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_all_info': {  # هندلر برای ثبت تمام لاگ‌های INFO و بالاتر در یک فایل کلی
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'all_info.log'),
            'maxBytes': 1024 * 1024 * 20,  # 20 مگابایت
            'backupCount': 2,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },

    'loggers': {
        '': {
            # Root logger: لاگر ریشه، هر لاگی که توسط لاگرهای دیگر مدیریت نشود، به اینجا می‌رسد (اگر propagate = True باشد)
            'handlers': ['console', 'file_errors', 'file_all_info'],
            'level': 'DEBUG',  # در محیط توسعه، روت را روی DEBUG بگذارید تا چیزی از دست نرود
            'propagate': False,  # بسیار مهم: از تکرار لاگ‌ها در لاگر پیش‌فرض پایتون جلوگیری می‌کند
        },
        'django': {  # لاگر مربوط به پیام‌های داخلی جنگو
            'handlers': ['file_django_errors', 'console'],  # خطاهای جنگو را در کنسول هم نشان بده
            'level': 'INFO',  # سطح اطلاعاتی جنگو
            'propagate': False,
        },
        # 'django.db.backends': { # لاگر مربوط به کوئری‌های دیتابیس
        #     'handlers': ['console'], # فقط در کنسول نشان داده شود تا فایل‌ها پر نشوند
        #     'level': 'DEBUG', # سطح دیباگ برای دیدن جزئیات کوئری‌ها
        #     'propagate': False, # از انتشار این لاگ‌های پرحجم به سایر هندلرها جلوگیری می‌کند
        # },
        'django.db.backends': {  # این قسمت رو ویرایش کنید
            'handlers': [],  # خالی کردن لیست هندلرها
            'level': 'DEBUG',  # سطحش رو DEBUG نگه می‌داریم برای زمانی که نیاز به دیباگ داریم
            'propagate': False,  # همچنان propagate رو False نگه می‌داریم تا به روت لاگر نرن
        },
        'budgets': {  # لاگر مخصوص اپ 'budgets' شما
            'handlers': ['console', 'file_budgets_debug', 'file_errors'],
            # هم در کنسول، هم در فایل دیباگ خودش، هم خطاهایش در فایل خطاهای کلی
            'level': 'DEBUG',  # همه پیام‌های دیباگ را برای اپ 'budgets' ثبت کن
            'propagate': False,
        },
        # اگر اپلیکیشن‌های دیگری دارید که می‌خواهید لاگ‌هایشان را جداگانه مدیریت کنید، اینجا اضافه کنید:
        # 'accounts': {
        #     'handlers': ['console', 'file_all_info'],
        #     'level': 'INFO',
        #     'propagate': False,
        # },
    },
}



JALALI_SETTINGS = {
    "ADMIN_JS_STATIC_FILES": [
        "admin/jquery.ui.datepicker.jalali/scripts/jquery-1.10.2.min.js",
        "admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.core.js",
        "admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc.js",
        "admin/jquery.ui.datepicker.jalali/scripts/calendar.js",
        "admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc-fa.js",
        "admin/main.js",
    ],
    "ADMIN_CSS_STATIC_FILES": {
        "all": [
            "admin/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css",
            "admin/css/main.css",
        ]
    },
}

