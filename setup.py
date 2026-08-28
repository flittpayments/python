import re
from setuptools import find_packages, setup

desc = """
    Flitt python sdk.
    Docs   - https://https://docs.flitt.com/
    README - https://https://github.com/flittpayments/python/blob/master/README.md
  """

requires_list = [
    'requests>=2.31.0',
    'six>=1.12'
]

# Read the version directly out of configuration.py's source text rather than
# importing the package, so setup.py works even before its own dependencies
# are installed (and can never drift from flittpayments.__version__).
with open('flittpayments/configuration.py') as f:
    __version__ = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", f.read()).group(1)

setup(
    name='flittpayments',
    version=__version__,
    url='https://github.com/flittpayments/python/',
    license='MIT',
    description='Python SDK for Flitt clients.',
    long_description=desc,
    author='Dmitriy Miroshnikov',
    packages=find_packages(where='.', exclude=('tests*',)),
    install_requires=requires_list,
    classifiers=[
        'Environment :: Web Environment',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ])
