#!/usr/bin/env python

"""
Bugsnag
=======

The official Python notifier for `Bugsnag <https://bugsnag.com/>`_.
Provides support for automatically capturing and sending exceptions
in your Django and other Python apps to Bugsnag, to help you find
and solve your bugs as fast as possible.
"""

import os
from setuptools import setup, find_packages

# Read version from VERSION file
with open(os.path.join(os.path.dirname(__file__), 'VERSION'), 'r') as f:
    version = f.read().strip()

setup(
    name='bugsnag',
    version=version,
    description='Automatic error monitoring for django, flask, etc.',
    long_description=__doc__,
    author='Simon Maynard',
    author_email='simon@bugsnag.com',
    url='https://bugsnag.com/',
    license='MIT',
    python_requires='>=3.5, <4',
    packages=find_packages(include=['bugsnag', 'bugsnag.*']),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development'
    ],
    package_data={
        'bugsnag': ['py.typed'],
    },
    test_suite='tests',
    install_requires=['webob'],
    extras_require={
        'flask': []
    }
)
