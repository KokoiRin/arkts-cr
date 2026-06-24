from pathlib import Path

from setuptools import find_packages, setup


setup(
    name="cr",
    version="0.1.0",
    description="Lightweight CLI for reviewing Git diffs and code outlines.",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    entry_points={"console_scripts": ["cr=cr.cli:main"]},
)
