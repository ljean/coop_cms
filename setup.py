#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""package the lib"""

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

VERSION = __import__('coop_cms').__version__

import os


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name='apidev-coop_cms',
    version=VERSION,
    description='Small CMS built around a tree navigation open to any django models',
    packages=find_packages(),
    include_package_data=True,
    author='Luc Jean',
    author_email='ljean@apidev.fr',
    license='BSD',
    zip_safe=False,
    install_requires=[
        'django >= 2.2.13',
        'django-extensions',
        'sorl-thumbnail',
        'apidev-coop_colorbox >= 1.6.0',
        'apidev-coop_bar >= 1.6.0',
        'coop_html_editor >= 1.4.0',
        'feedparser',
        'beautifulsoup4',
        'model_mommy',
        'unicode-slugify',
    ],
    long_description=open('README.rst').read(),
    url='https://github.com/ljean/coop_cms/',
    download_url='https://github.com/ljean/coop_cms/tarball/master',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
