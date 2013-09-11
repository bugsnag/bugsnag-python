#!/usr/bin/env python

"""
Bugsnag
=======

The official Python notifier for `Bugsnag <https://bugsnag.com/>`_.
Provides support for automatically capturing and sending exceptions
in your Django and other Python apps to Bugsnag, to help you find
and solve your bugs as fast as possible.
"""

from setuptools import setup, find_packages

setup(
    name='bugsnag',
    version='1.2.7',
    description='Official Python notifier for Bugsnag (https://bugsnag.com).',
    long_description=__doc__,
    author='Simon Maynard',
    author_email='simon@bugsnag.com',
    url='https://bugsnag.com/',
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Topic :: Software Development'
    ],
    install_requires=["werkzeug", "blinker"],
)