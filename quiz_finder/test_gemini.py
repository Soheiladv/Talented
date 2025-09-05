# test_gemini.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

print("--- شروع تست ارتباط با Gemini ---")

# ۱. بارگذاری متغیرهای محیطی از فایل .env
# این خط به دنبال فایل .env در همین پوشه (ریشه پروژه) می‌گردد
load_dotenv()
print("فایل .env بارگذاری شد.")

# ۲. خواندن کلید API از متغیرهای محیطی
# os.getenv به دنبال متغیری به نام 'GOOGLE_API_KEY' در محیط می‌گردد
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("\n!!! خطا: متغیر GOOGLE_API_KEY در فایل .env یافت نشد یا خالی است.")
    print("لطفاً مطمئن شوید که فایل .env در ریشه پروژه وجود دارد و حاوی خطی مانند GOOGLE_API_KEY=\"AIza...\" است.")
else:
    print("کلید API با موفقیت از .env خوانده شد.")
    try:
        # ۳. پیکربندی کتابخانه Gemini با کلید API
        genai.configure(api_key=api_key)
        print("کتابخانه Gemini با کلید API پیکربندی شد.")

        # ۴. انتخاب مدل
        # از مدل 'gemini-1.5-flash' استفاده می‌کنیم که جدیدتر و بهینه‌تر است
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print(f"مدل '{model.model_name}' انتخاب شد.")

        # ۵. ارسال پرامپت و دریافت پاسخ
        prompt = "Explain how AI works in a few words"
        print(f"\nارسال پرامپت: '{prompt}'")

        response = model.generate_content(prompt)

        # ۶. چاپ پاسخ دریافت شده
        print("\n--- پاسخ دریافت شده از Gemini ---")
        print(response.text)
        print("---------------------------------")

    except Exception as e:
        print(f"\n!!! خطا در هنگام ارتباط با Gemini: {e}")
        print("لطفاً موارد زیر را بررسی کنید:")
        print("۱. آیا کلید API شما صحیح و فعال است؟")
        print("۲. آیا به اینترنت متصل هستید؟")
        print("۳. آیا پکیج google-generativeai به درستی نصب شده است؟")

print("\n--- تست به پایان رسید ---")