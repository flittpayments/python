import re
from setuptools import find_packages, setup

desc = """
    Flitt python sdk.
    Docs   - https://docs.flitt.com/
    README - https://github.com/flittpayments/python/blob/main/README.md
  """

requires_list = [
    'requests>=2.20.0,<2.22.0; python_version == "3.4"',
    'requests>=2.20.0,<2.28.0; python_version < "3.7" and '
    'python_version != "3.4"',
    'requests>=2.31.0; python_version >= "3.7"',
    'six>=1.12'
]

extras_require = {
    'async': ['httpx2>=2.0.0,<3.0.0'],
}

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
    package_data={'flittpayments': ['*.pyi', 'py.typed']},
    include_package_data=True,
    install_requires=requires_list,
    extras_require=extras_require,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    classifiers=[
        'Environment :: Web Environment',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ])
