#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for selenium_browser."""
from setuptools import setup, find_packages

__version__ = '0.3.0'

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

tests_require = [
    'pytest >= 7.4.3',
    'pytest-retry >= 1.5.0',
    'pytest-mock >= 3.12.0',
    'pytest-cov >= 4.1.0',
    'flake8 >= 6.1.0',
    'pylint >= 3.0.3',
    'mock >= 5.1.0',
    'freezegun >= 1.4.0',
    'pproxy >= 2.7.8',
]

setup(
    name='webdriver-browser',
    # dev[n] .alpha[n] .beta[n] .rc[n] .post[n] .final
    version=__version__,
    author='Invoker Bot',
    author_email='invoker-bot@outlook.com',
    description='More convenient methods for creating multiple selenium browsers.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/invoker-bot/selenium_browser',
    packages=find_packages(),
    classifiers=[
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.10',
    install_requires=[
        'psutil >= 5.9.8',
        'urllib3 ~= 1.26.18',
        'selenium >= 4.15.0',
        'blinker >=1.4, < 1.8.0',
        'selenium-wire >= 5.1.0',
        'webdriver_manager >= 4.0.1',
        'undetected-chromedriver >= 3.5.5',
        'tenacity >= 8.2.3',
        'requestium >= 0.4.0',
        'requests >= 2.32.3',
    ],
    setup_requires=['pytest-runner >= 6.0.1'],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },
    license='MIT',
    aliases={
        'test': 'pytest',
    }
    # entry_points={}
)
