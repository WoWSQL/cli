"""Setup script for WoWSQL CLI."""

from setuptools import setup, find_packages
from pathlib import Path
import sys

# Read version from __init__.py
def get_version():
    """Get version from wowsql_cli/__init__.py."""
    init_file = Path(__file__).parent / "wowsql_cli" / "__init__.py"
    if init_file.exists():
        with open(init_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="wowsql-cli",
    version=get_version(),
    description="WoWSQL Command Line Interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="WoWSQL Team",
    author_email="support@wowsql.com",
    url="https://github.com/wowsql/cli",
    project_urls={
        "Documentation": "https://wowsql.com/docs",
        "Source": "https://github.com/wowsql/cli",
        "Tracker": "https://github.com/wowsql/cli/issues",
    },
    packages=find_packages(),
    install_requires=[
        "click>=8.1.7",
        "rich>=13.7.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "docker>=6.1.0",
        "keyring>=24.3.0",
        "cryptography>=41.0.7",
        "pygments>=2.17.2",
    ],
    entry_points={
        "console_scripts": [
            "wowsql=wowsql_cli.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    keywords="wowsql cli database Postgres backend api",
)

