import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../.."))

project = "YbYráSTAC"
author = "Celso H. L. Silva Junior"
copyright = f"{datetime.now().year}, {author}"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_gallery.gen_gallery",
]

html_theme = "sphinx_book_theme"
html_title = "YbYráSTAC"
html_static_path = ["_static"]
source_suffix = [".rst", ".md"]

sphinx_gallery_conf = {
    "examples_dirs": "../../examples",
    "gallery_dirs": "auto_examples",
    "filename_pattern": r"/\d+_",
}

intersphinx_mapping = {
    "python":    ("https://docs.python.org/3", None),
    "xarray":    ("https://docs.xarray.dev/en/stable/", None),
    "rioxarray": ("https://corteva.github.io/rioxarray/stable/", None),
    "pystac":    ("https://pystac.readthedocs.io/en/stable/", None),
}
