import os, sys
sys.path.insert(0, os.path.abspath('../..'))

project   = 'Dark Mirror'
copyright = '2026, Yasser KHADIRI - ENSAM Meknes'
author    = 'Yasser KHADIRI'
release   = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

exclude_patterns = []
html_theme       = 'sphinx_rtd_theme'