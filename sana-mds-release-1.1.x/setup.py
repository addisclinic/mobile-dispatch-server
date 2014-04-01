#!/usr/bin/env python

# Setuptools module description for the Moca Dispatch Server

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

#packages = find_packages(exclude='tests')
packages = ['moca',]

setup(name='Moca-MDS',
      version='1.0',
      description='The Moca Dispatch Server -- a Django middleware layer for the Moca project.',
      long_description="""
The Moca Dispatch Server (MDS) is a middleware layer in for the Moca project
which is used to abstract the connection between Moca clients and the backend
EMR.
""",
      author='Moca Mobile',
      author_email='moca-developers@mit.edu',
      url='http://www.mocamobile.org',
      license = "BSD",
      include_package_data = True,
      packages=packages,
      scripts=['scripts/requirements.txt',],
      package_dir = {
        'moca': 'moca',
        },
      package_data={'moca': ['templates/*', 'media/*', 'settings.py.tmpl']},
      install_requires=['Django>=1.1.1',],
      classifiers = [
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        ],
      )
