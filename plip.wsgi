#!/usr/bin/env python
import sys
import logging
import os


logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from plip import app as application
