import esipy
import io

from setuptools import setup

# install requirements
install_requirements = [
    "requests",
    "pyswagger >= 0.8.39",
    "six",
    "pytz",
]

# test requirements
test_requirements = [
    "coverage",
    "coveralls",
    "httmock",
    "nose",
    "mock",
    "future",
    "python-memcached",
    "redis",
] + install_requirements

with io.open('README.rst', encoding='UTF-8') as reader:
    readme = reader.read()

setup(
    name='EsiPy',
    version=esipy.__version__,
    packages=['esipy'],
    url='https://github.com/Kyria/EsiPy',
    license='BSD 3-Clause License',
    author='Kyria',
    author_email='anakhon@gmail.com',
    description='Swagger Client for the ESI API for EVE Online',
    long_description=readme,
    install_requires=install_requirements,
    extras_require={
        ':python_version == "2.7"': ['futures']
    },
    tests_require=test_requirements,
    test_suite='nose.collector',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
    ]
)
