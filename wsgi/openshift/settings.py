# -*- coding: utf-8 -*-
# Django settings for openshift project.
import imp, os

# a setting to determine whether we are running on OpenShift
ON_OPENSHIFT = False
if os.environ.has_key('OPENSHIFT_REPO_DIR'):
    ON_OPENSHIFT = True

#add by bone
if not ON_OPENSHIFT:
    STATIC_PATH=os.path.join(os.path.dirname(__file__), "static")
    CKEDITOR_UPLOAD_PATH = os.path.join(os.path.dirname(__file__),"static/ckupload").replace('\\','/')
else:
    #os.path.join(PROJECT_DIR, '..', 'static/ckupload')
    #CKEDITOR_UPLOAD_PATH = os.path.join(os.path.dirname(__file__),"../static/media/ckupload").replace('\\','/')    
    CKEDITOR_UPLOAD_PATH = os.path.join(os.environ.get('OPENSHIFT_DATA_DIR', ''),"upload","ckupload").replace('\\','/')

# This setting specifies a URL prefix to media uploaded through CKEditor.
#(If CKEDITOR_UPLOAD_PREFIX is not provided, the media URL will fall back to MEDIA_URL 
#with the difference of MEDIA_ROOT and the uploaded resource's full path and filename appended.)

CKEDITOR_UPLOAD_PREFIX = "/media/ckupload/"


#By specifying a set named default you'll be applying its settings to all RichTextField 
#and CKEditorWidget objects for which config_name has not been explicitly defined

#CKEDITOR_CONFIGS = {
#    'default': {
#        'toolbar': 'Full',
#        'height': 300,
#        'width': 300,
#    },
#}

#add over

#add by bone
DISQUS_USER_API_KEY="njGHpOU7w6CEyA46mgjZ83Jid0maj5Bk01tN73WiNeN403Rg1mr7ijdEG978z0oQ"
DISQUS_FORUM_SHORTNAME="dmood"
TEMPLATE_CONTEXT_PROCESSORS=(
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	"django.core.context_processors.request",
)
#-------add over

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

if ON_OPENSHIFT:
    # os.environ['OPENSHIFT_DB_*'] variables can be used with databases created
    # with rhc app cartridge add (see /README in this git repo)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'. 
            'NAME': 'blog',  # Or path to database file if using sqlite3. 
            'USER': os.environ["OPENSHIFT_DB_USERNAME"],                      # Not used with sqlite3. 
            'PASSWORD': os.environ["OPENSHIFT_DB_PASSWORD"],                  # Not used with sqlite3. 
            'HOST': os.environ["OPENSHIFT_DB_HOST"],       # Set to empty string for localhost. Not used with sqlite3. 
            'PORT': os.environ["OPENSHIFT_DB_PORT"],   # Set to empty string for default. Not used with sqlite3. 
        }
    }
    # Sphinx 0.9.9
    SPHINX_API_VERSION = 0x116
    DATABASE_ENGINE = 'mysql'          # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
    DATABASE_NAME = os.environ["OPENSHIFT_APP_NAME"]             # Or path to database file if using sqlite3.
    DATABASE_USER = os.environ["OPENSHIFT_DB_USERNAME"]          # Not used with sqlite3.
    DATABASE_PASSWORD = os.environ["OPENSHIFT_DB_PASSWORD"]         # Not used with sqlite3.
    DATABASE_HOST = os.environ["OPENSHIFT_DB_HOST"]            # Set to empty string for localhost. Not used with sqlite3.
    DATABASE_PORT = os.environ["OPENSHIFT_DB_PORT"]            # Set to empty string for default. Not used with sqlite3.

    #This server is used to sphinx communication
    #In djangosphinx model.py file,you will see:
    # server settings
    #SPHINX_SERVER           = getattr(settings, 'SPHINX_SERVER', 'localhost')
    #SPHINX_PORT             = int(getattr(settings, 'SPHINX_PORT', 3312))
    SPHINX_SERVER=os.environ["OPENSHIFT_DATA_DIR"]+"app/sphinx/data/searchd.sock" #This means that you use socket to communicate


else:
    DATABASES = {
	    'default': {
		'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
		'NAME': 'Articles',                      # Or path to database file if using sqlite3. 'NAME': 'books',
		'USER': 'spark',                      # Not used with sqlite3. 'USER': 'root',   
		'PASSWORD': '',                  # Not used with sqlite3. 'PASSWORD': 'lanzi520',
		'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
		'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
	    }
    }
    # Sphinx 0.9.9
    SPHINX_API_VERSION = 0x116
    DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
    DATABASE_NAME = 'books'             # Or path to database file if using sqlite3.
    DATABASE_USER = 'root'             # Not used with sqlite3.
    DATABASE_PASSWORD = 'lanzi520'         # Not used with sqlite3.
    DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
    DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

    #This server is used to sphinx communication
    #In djangosphinx model.py file,you will see:
    # server settings
    #SPHINX_SERVER           = getattr(settings, 'SPHINX_SERVER', 'localhost')
    #SPHINX_PORT             = int(getattr(settings, 'SPHINX_PORT', 3312))
    SPHINX_SERVER="/home/lan/openshift/blog/data/searchd.sock" #This means that you use socket to communicate

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
###TIME_ZONE = 'America/Chicago'
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html

#add by bone
#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-cn'
LANGUAGES = (
    ('zh-cn', u'简体中文'),
    #('zh-tw', u'繁體中文'),
    ('en', 'English'),
)
#add over

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.environ.get('OPENSHIFT_DATA_DIR', '')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_DIR, '..', 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), "mystatic"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make a dictionary of default keys
default_keys = { 'SECRET_KEY': 'vm4rl5*ymb@2&d_(gc$gb-^twq9w(u69hi--%$5xrh!xk(t%hw' }

# Replace default keys with dynamic values if we are in OpenShift
use_keys = default_keys
if ON_OPENSHIFT:
    imp.find_module('openshiftlibs')
    import openshiftlibs
    use_keys = openshiftlibs.openshift_secure(default_keys)

# Make this unique, and don't share it with anybody.
SECRET_KEY = use_keys['SECRET_KEY']

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'openshift.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    'django.contrib.humanize',
    'djangosphinx',	
    'ckeditor', 
    'articles',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
