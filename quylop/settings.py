"""
Django settings for quylop project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-p_==j%3i#j_ref8m77mw=v2dj7rdvycx(z5pd(b#kd-(yfwtm6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['fundflow.com', '127.0.0.1', 'localhost', '*'] 

# ==========================================
# 1. KHAI BÁO APP (INSTALLED_APPS)
# ==========================================
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', 

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.facebook',

    'captcha',  # App Captcha
    'quanlyquy', 
]

# --- CẤU HÌNH BẢO MẬT GOOGLE RECAPTCHA V2 ---
# Đảm bảo 2 dòng này nằm ngoài ngoặc vuông của INSTALLED_APPS
RECAPTCHA_PUBLIC_KEY = '6LdkaoUsAAAAAPFYnV6w0rTnOX7uAbVA97NIBZGJ'
RECAPTCHA_PRIVATE_KEY = '6LdkaoUsAAAAAKXc5-j8CfG9DAHPWZby35flB29F'
# CẤU HÌNH GỬI MAIL THẬT QUA GMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tranquanquan025@gmail.com' # Email dùng để gửi đi
EMAIL_HOST_PASSWORD = 'nmecpnxudgxivmrp' # Dán 16 ký tự App Password vào đây
DEFAULT_FROM_EMAIL = 'FundFlow PRO <tranquanquan025@gmail.com>'

SITE_ID = 1
# ==========================================
# 2. MIDDLEWARE & BACKENDS
# ==========================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Middleware bắt buộc của Allauth
    'allauth.account.middleware.AccountMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ROOT_URLCONF = 'quylop.urls'

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

WSGI_APPLICATION = 'quylop.wsgi.application'

# ==========================================
# 3. DATABASE & CUSTOM USER
# ==========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Chỉ định User Model tùy chỉnh của ông
AUTH_USER_MODEL = 'quanlyquy.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]
# Bỏ qua trang trung gian "Sign In Via Google", bấm nút là bay sang Google luôn
SOCIALACCOUNT_LOGIN_ON_GET = True
# Tự động tạo user mới từ thông tin Google mà không bắt điền thêm form
SOCIALACCOUNT_AUTO_SIGNUP = True

# ==========================================
# 4. NGÔN NGỮ, FORMAT & ĐIỀU HƯỚNG
# ==========================================
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Format tiền tệ Việt Nam (1.000.000)
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
NUMBER_GROUPING = 3

# Điều hướng Đăng nhập
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'login_redirect' # Trạm điều hướng phân quyền của ông
LOGOUT_REDIRECT_URL = 'login'

# ==========================================
# 5. STATIC & MEDIA
# ==========================================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# 6. GIAO DIỆN ADMIN (UNFOLD)
# ==========================================
UNFOLD = {
    "SITE_TITLE": "FundSmart Pro",
    "SITE_HEADER": "Quản trị FundSmart",
    "SITE_SYMBOL": "account_balance",
    "COLORS": {
        "primary": {
            "50": "238, 242, 255",
            "100": "224, 231, 255",
            "200": "199, 210, 254",
            "300": "165, 180, 252",
            "400": "129, 140, 248",
            "500": "99, 102, 241", 
            "600": "79, 70, 229",
            "700": "67, 56, 202",
            "800": "55, 48, 163",
            "900": "49, 46, 129",
            "950": "30, 27, 75",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
    },
    "DASHBOARD_CALLBACK": "quanlyquy.dashboard.dashboard_callback",
}