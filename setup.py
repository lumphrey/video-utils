from setuptools import setup, find_packages
import os
import re


def read_version():
    """Read the version from the package __init__.py file without importing the package."""
    here = os.path.abspath(os.path.dirname(__file__))
    init_py = open(os.path.join(here, 'utils', '__init__.py')).read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", init_py, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="video_utils",
    version=read_version(),
    packages=find_packages(),
    entry_points={'console_scripts': ['video-utils-cli=utils.concat:main']}
)
