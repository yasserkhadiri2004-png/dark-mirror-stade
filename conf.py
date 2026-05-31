import os, sys
sys.path.insert(0, os.path.abspath('../..'))

project   = 'Dark Mirror'
copyright = '2026, Yasser KHADIRI — ENSAM Meknes'
author    = 'Yasser KHADIRI'
release   = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'myst_parser',
]

templates_path   = ['_templates']
exclude_patterns = []
html_theme       = 'sphinx_rtd_theme'
html_static_path = ['_static']
source_suffix    = {'.rst': 'restructuredtext', '.md': 'markdown'}

html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'navigation_depth': 4,
    'style_nav_header_background': '#C1272D',
}
