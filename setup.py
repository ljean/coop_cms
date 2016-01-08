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


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


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
        'django >= 1.8.8, < 1.9',  # In road to 1.9
        'django-floppyforms',
        'django-extensions',
        'sorl-thumbnail',
        'apidev-coop_colorbox >= 1.1.1',
        'apidev-coop_bar >= 1.2.0',
        'apidev-djaloha >= 1.0.4',
        'feedparser',
        'beautifulsoup4',
        'django-filetransfers',
        'model_mommy',
    ],
    dependency_links=[
        'git+https://github.com/ljean/coop-colorbox.git@1aefa1eefaace426e8570463b2b5cd6ad0e04be4#egg=apidev_coop_colorbox-dev',
        'git+https://github.com/ljean/djaloha.git@82c9b25054350f76b47e5aa40a6d36414174bcf9#egg=apidev_djaloha-dev',
        'git+https://github.com/ljean/coop-bar.git@3b7fae26c0e4c999fa1736f417b49d3983231364#egg=coop_bar-dev',
    ],
    long_description=open('README.rst').read(),
    url='https://github.com/ljean/coop_cms/',
    download_url='https://github.com/ljean/coop_cms/tarball/master',
    classifiers=[
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
