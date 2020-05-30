#!/bin/env python3

from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='borgmacator',
    version='0.0.1',
    description='A GNOME AppIndicator for Borgmatic',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/N-Coder/borgmacator',
    author='Niko Fink',
    author_email='borgmacator@niko.fink.bayern',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: Gnome',
        'Operating System :: Unix',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Desktop Environment :: Gnome',
        'Topic :: System :: Archiving :: Backup',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='borg borgmatic backup appindicator indicator gnome',
    packages=find_packages(),
    python_requires='>=3.5, <4',
    install_requires=['PyGObject', 'pystemd', 'python-dateutil', 'requests', 'sh', 'appdirs'],
    entry_points={
        'console_scripts': [
            'borgmacator=borgmacator.main:main',
            'borgmacator-autostart=borgmacator.install:install',
            'borgmacator-restart=borgmacator.install:restart',
        ],
    },
    zip_safe=False,
    package_data={
        'borgmacator': ["img/*.svg"],
    }
)
