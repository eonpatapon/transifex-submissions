#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
    Transifex submissions

    Basic VCS integration with Transifex

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import os, sys
from setuptools import setup, find_packages
from django import VERSION
from django.core.management.commands.compilemessages import compile_messages

sys.path.insert(0, os.path.abspath('txsubmissions'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'txsubmissions.settings'

# compile language files at installation
if VERSION[1] > 2:
    compile_messages(sys.stderr)
else:
    compile_messages()

setup(
    name='txsubmissions',
    version = '0.1',
    description = "Transifex submissions",
    author = "Jean-Philippe Braun",
    author_email = "jpbraun@mandriva.com",
    maintainer = "Jean-Philippe Braun",
    maintainer_email = "jpbraun@mandriva.com",
    url = "http://www.mandriva.com",
    packages = find_packages(),
    include_package_data = True,
)
