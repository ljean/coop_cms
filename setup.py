#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

VERSION = __import__('coop_cms').__version__

import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'apidev-coop_cms',
    version = VERSION,
    description = 'Small CMS built around a tree navigation open to any django models',
    packages = [
        'coop_cms',
        'coop_cms.apps',
        'coop_cms.apps.basic_cms',
        'coop_cms.apps.basic_cms.migrations',
        'coop_cms.apps.coop_bootstrap',
        'coop_cms.apps.coop_bootstrap.templatetags',
        'coop_cms.apps.demo_cms',
        'coop_cms.apps.demo_cms.migrations',
        'coop_cms.apps.rss_sync',
        'coop_cms.apps.rss_sync.management',
        'coop_cms.apps.rss_sync.management.commands',
        'coop_cms.apps.rss_sync.migrations',
        'coop_cms.apps.test_app',
        'coop_cms.management',
        'coop_cms.management.commands',
        'coop_cms.migrations',
        'coop_cms.templatetags',
    ],
    include_package_data = True,
    author = 'Luc Jean',
    author_email = 'ljean@apidev.fr',
    license = 'BSD',
    zip_safe = False,
    install_requires = [
        'django >= 1.5',
        'south',
        'django-floppyforms',
        'django-extensions',
        'sorl-thumbnail',
        'apidev-coop_colorbox',
        'apidev-coop_bar',
        'apidev-djaloha >= 1.0.2',
        'django-pagination',
        'feedparser',
        'beautifulsoup4',
        "django-contrib-requestprovider",
        'django-filetransfers',
        'model_mommy',
    ],
    long_description = open('README.rst').read(),
    url = 'https://github.com/ljean/coop_cms/',
    download_url = 'https://github.com/ljean/coop_cms/tarball/master',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'Natural Language :: English',
        'Natural Language :: French',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],

)

