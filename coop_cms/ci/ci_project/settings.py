# -*- coding: utf-8 -*-
"""project settings"""

import os.path
import sys

from django import VERSION as DJANGO_VERSION
from django.urls import reverse_lazy

DEBUG = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_db',
        'USER': 'apidev',
        'PASSWORD': 'apidev',
        'HOST': 'localhost',
        # 'PORT': 5432,
        'ATOMIC_REQUESTS': True,
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English')),
    ('fr', gettext('Français')),
    ('en-us', gettext('American')),
    ('ru', gettext('Russian')),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.abspath(PROJECT_PATH + '/public/media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.abspath(PROJECT_PATH+'/public/static/')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'drone-ci'

# List of callables that know how to import templates from various sources.

if DJANGO_VERSION > (1, 9):
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                os.path.join(PROJECT_PATH, 'templates'),
            ],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]
else:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

    TEMPLATE_DIRS = (
        # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
        # Always use forward slashes, even on Windows.
        # Don't forget to use absolute paths, not relative paths.
        os.path.abspath(PROJECT_PATH + '/templates'),
    )

    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.template.context_processors.debug",
        "django.template.context_processors.i18n",
        "django.template.context_processors.request",
        "django.template.context_processors.media",
        "django.template.context_processors.static",
        "django.contrib.messages.context_processors.messages",
    )


MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'coop_cms.utils.RequestMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'application'


AUTHENTICATION_BACKENDS = (
    'coop_cms.perms_backends.ArticlePermissionBackend',
    'coop_cms.apps.email_auth.auth_backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend', # Django's default auth backend
)

LOCALE_PATHS = (
    PROJECT_PATH + '/locale/',
)

TEST_RUNNER = 'coop_cms.test_runners.SafeMediaDiscoverRunner'

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = reverse_lazy('login')

ACCOUNT_ACTIVATION_DAYS = 7

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = (
    # contribs
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    # 3rd parties
    'django_extensions',
    'floppyforms',
    'sorl.thumbnail',
    'django_registration',

    # externals
    'coop_html_editor',
    'colorbox',
    'coop_cms',
    'coop_bar',
    # choose one between in basic_cms and demo_cms
    'coop_cms.apps.basic_cms',
    # 'coop_cms.apps.demo_cms',
    'coop_cms.apps.email_auth',
    'coop_cms.apps.newsletters',
    'coop_cms.apps.rss_sync',

    'django.contrib.admin',
    'django.contrib.admindocs',
)

# if (len(sys.argv) > 1) and (not sys.argv[1] in ('schemamigration', 'datamigration', 'makemigrations')):
#     INSTALLED_APPS = ('modeltranslation', ) + INSTALLED_APPS

if 'coop_cms.apps.basic_cms' in INSTALLED_APPS:
    COOP_HTML_EDITOR_LINK_MODELS = ('basic_cms.Article',)
elif 'coop_cms.apps.demo_cms' in INSTALLED_APPS:
    COOP_HTML_EDITOR_LINK_MODELS = ('demo_cms.Article',)
    COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.Article'
    COOP_CMS_ARTICLE_FORM = 'coop_cms.apps.demo_cms.forms.ArticleForm'

COOP_CMS_ARTICLE_LOGO_SIZE = "950x250"
COOP_CMS_NEWSLETTER_TEMPLATES = (
    ('basic_newsletter.html', 'Basic'),
)
COOP_CMS_ARTICLE_TEMPLATES = (
    ('standard.html', 'Standard'),
)
COOP_CMS_FROM_EMAIL = ''
COOP_CMS_TEST_EMAILS = ('"Luc JEAN - Apidev" <ljean@apidev.fr>', )
COOP_CMS_SITE_PREFIX = ''
COOP_CMS_REPLY_TO = 'ljean@apidev.fr'
COOP_CMS_TITLE_OPTIONAL = True


if len(sys.argv) > 1 and 'test' == sys.argv[1]:
    INSTALLED_APPS = INSTALLED_APPS + ('coop_cms.apps.test_app', )

# import warnings
# warnings.filterwarnings('ignore', r"django.contrib.localflavor is deprecated")


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'coop_cms': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'colorbox': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

try:
    from local_settings import *  # pylint: disable=W0401,W0614
except ImportError:
    pass
