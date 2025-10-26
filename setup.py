#!/usr/bin/env python3
"""
Setup script for Smart Glasses Demo system
"""

from setuptools import setup, find_packages
import sys
import os

# Read the README file for long description
def read_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='smart-glasses-demo',
    version='1.0.0',
    description='A production-ready system for video capture, Telegram integration, and computer vision analysis for industrial hazard detection',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Smart Glasses Team',
    author_email='admin@smartglasses.com',
    url='https://github.com/yourorg/smart-glasses-demo',
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Multimedia :: Video :: Capture',
        'Topic :: Communications :: Chat',
    ],
    keywords=['computer-vision', 'video-analysis', 'telegram-bot', 'industrial-safety', 'oil-leak-detection', 'hazard-detection'],
    entry_points={
        'console_scripts': [
            'smart-glasses=main:main',
        ],
    },
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-asyncio>=0.21.0',
            'black>=22.0',
            'flake8>=4.0',
            'mypy>=0.991',
        ],
        'gpu': [
            'torch[cuda]',
            'torchvision[cuda]',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/yourorg/smart-glasses-demo/issues',
        'Source': 'https://github.com/yourorg/smart-glasses-demo',
        'Documentation': 'https://smart-glasses-demo.readthedocs.io/',
    },
)
