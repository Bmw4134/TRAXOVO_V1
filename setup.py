#!/usr/bin/env python3
"""
Setup script for TRAXOVO Watson Intelligence Platform
"""

from setuptools import setup, find_packages

setup(
    name="traxovo-watson-intelligence",
    version="1.0.0",
    description="Advanced autonomous system intelligence platform with Watson Command Console",
    long_description="An enterprise-level AI system management platform with distributed computational analysis capabilities.",
    long_description_content_type="text/plain",
    author="TRAXOVO Watson Intelligence",
    author_email="watson@traxovo.com",
    url="https://github.com/traxovo/watson-intelligence",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "Flask>=2.3.3",
        "Flask-SQLAlchemy>=3.1.1", 
        "Flask-Login>=0.6.3",
        "gunicorn>=21.2.0",
        "Werkzeug>=2.3.7",
        "psycopg2-binary>=2.9.7",
        "python-dotenv>=1.0.0",
        "SQLAlchemy>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Enterprise",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Framework :: Flask",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "watson-start=main:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)