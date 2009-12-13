## this file is generated from settings in build.vel

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# from options["setup"] in build.vel
config = {'package_data': {'lamson': ['data/prototype.zip']}, 'description': 'Lamson is a modern Pythonic mail server built like a web application server.', 'author': 'Zed A. Shaw', 'url': 'http://pypi.python.org/pypi/lamson', 'download_url': 'http://pypi.python.org/pypi/lamson', 'author_email': 'zedshaw@zedshaw.com', 'version': '1.0pre10', 'scripts': ['bin/lamson'], 'install_requires': ['chardet', 'jinja2', 'mock', 'nose', 'python-daemon'], 'packages': ['lamson', 'lamson.handlers'], 'name': 'lamson'}
setup(**config)

