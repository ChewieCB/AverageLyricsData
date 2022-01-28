from setuptools import setup, find_packages

setup(
    name='average_lyrics_data',
    version='0.1',
    author='Jack McCaffrey',
    author_email='jackmccaffrey96@gmail.com',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'asynctest',
        'backoff',
        'matplotlib',
        'musicbrainzngs',
        'PyQt5',
    ]
)