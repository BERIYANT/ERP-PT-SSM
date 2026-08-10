import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY=os.getenv('SECRET_KEY','dev-change-me')
DEBUG=os.getenv('DEBUG','1')=='1'
ALLOWED_HOSTS=os.getenv('ALLOWED_HOSTS','*').split(',')
INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','portal','erp']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','portal.middleware.JsonErrorMiddleware']
ROOT_URLCONF='ssm.urls'; TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.messages.context_processors.messages','portal.context.current_user','erp.context_processors.navigation']}}]
WSGI_APPLICATION='ssm.wsgi.application'
if os.getenv('DB_ENGINE','mysql')=='sqlite': DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':os.getenv('DB_NAME',BASE_DIR/'db.sqlite3')}}
else:
    # DB_* takes precedence; MYSQL_* keeps compatibility with the Flask deployment.
    # Local fallback defaults match a typical MAMP install: root/root on 127.0.0.1:3306.
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', os.getenv('MYSQL_DATABASE', 'ssm_portal')),
        'USER': os.getenv('DB_USER', os.getenv('MYSQL_USER', 'root')),
        'PASSWORD': os.getenv('DB_PASSWORD', os.getenv('MYSQL_PASSWORD', 'root')),
        'HOST': os.getenv('DB_HOST', os.getenv('MYSQL_HOST', '127.0.0.1')),
        'PORT': os.getenv('DB_PORT', os.getenv('MYSQL_PORT', '3306')),
        'OPTIONS': {'charset': 'utf8mb4'},
    }}
AUTH_USER_MODEL='portal.User'
LOGIN_URL='/login'; DEFAULT_AUTO_FIELD='django.db.models.AutoField'; USE_TZ=False; LANGUAGE_CODE='id'; TIME_ZONE='Asia/Jakarta'
STATIC_URL='/static/'; STATICFILES_DIRS=[BASE_DIR/'static']; MEDIA_ROOT=BASE_DIR/'static'/'uploads'; MEDIA_URL='/media/'; SESSION_COOKIE_AGE=28800
