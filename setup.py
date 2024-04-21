from setuptools import setup, find_packages

setup(
    name="video_utils",
    version='0.2',
    packages=find_packages(),
    entry_points={'console_scripts' : ['video-utils-cli=utils.concat:main']}
)