from setuptools import setup
from esipy import __version__ 

# install requirements
install_requirements = [
    "requests",
    "pyswagger",
    "six"
]

# test requirements
test_requirements = [
    "coverage",
    "coveralls",
    "httmock",
    "nose",
    "mock",
    "future",
    "python-memcached"
] + install_requirements

setup(
    name='EsiPy',
    version=__version__,
    packages=['esipy'],
    url='https://github.com/Kyria/EsiPy',
    license='BSD 3-Clause License',
    author='Kyria',
    author_email='anakhon@gmail.com',
    description='Swagger Client for the ESI API for EVE Online',
    install_requires=install_requirements,
    tests_require=test_requirements,
    test_suite='nose.collector',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: PyPy",
    ]
)
