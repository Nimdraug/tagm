#!/usr/bin/env python2
from setuptools import setup

setup(
    name = 'tagm',
    version = '0.2-dev',
    
    maintainer = u'Martin Hult\xe9n-Ashauer',
    maintainer_email = 'tagm@nimdraug.com',
    url = 'http://github.com/Nimdraug/tagm',
    license = 'MIT',
    description = 'A command and library for managing meta tags for arbitrary files',
    
    py_modules = [
        'tagm'
    ],
    entry_points = {
        'console_scripts': [
            'tagm = tagm:main'
        ]
    }

)
