from setuptools import find_packages, setup

desc = """
    Flitt python sdk. 
    Docs   - https://https://docs.flitt.com/
    README - https://https://github.com/flittpayments/python/blob/master/README.md
  """

requires_list = [
    'requests',
    'six'
]

setup(
    name='flittpayments',
    version='1.0.4',
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
