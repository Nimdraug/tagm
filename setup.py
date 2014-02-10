#!/usr/bin/env python2
from setuptools import setup

setup(
    name = 'tagm',
    version = '0.1-dev',
    py_modules = [
        'tagm'
    ],
    entry_points = {
        'console_scripts': [
            'tagm = tagm:main'
        ]
    }

)
