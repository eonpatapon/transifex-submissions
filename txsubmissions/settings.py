#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
    Transifex submissions - Global settings

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""


import os

PROJECT_DIR = os.path.dirname(__file__)

# Define where language files are to compile them
# at package installation
LOCALE_PATHS = (
    os.path.join(PROJECT_DIR),
)
