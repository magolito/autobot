#!/usr/bin/env python3
"""Rebuild the generated pages (results.html, plans.html). Run from anywhere:  python3 tools/build_pages.py"""
import runpy
from pathlib import Path
HERE = Path(__file__).resolve().parent
for script in ('build_results.py', 'build_plans.py'):
    runpy.run_path(str(HERE / script), run_name='__main__')
