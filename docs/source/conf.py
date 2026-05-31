import os, sys
sys.path.insert(0, os.path.abspath('../..'))

project   = 'Dark Mirror'
copyright = '2026, Yasser KHADIRI - ENSAM Meknes'
author    = 'Yasser KHADIRI'
release   = '1.0.0'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']

exclude_patterns = []
html_theme       = 'sphinx_rtd_theme'
html_logo        = None

html_theme_options = {
    'navigation_depth': 4,
    'style_nav_header_background': '#C1272D',
}