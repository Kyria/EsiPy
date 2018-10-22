---
layout: base
section: getting_started/installation
title: Installation
---
# How to install EsiPy

## Using `pip`

The **easiest and recommanded** way to install the library is by using the `pip` package manager.
```
pip install esipy
```

&nbsp;

## Using `setuptools`

You also can install it by downloading the latest sources [here](https://github.com/Kyria/EsiPy/releases/latest) and running
```
python setup.py install
```

&nbsp;

## Integrating the lib in your project

If you want to use EsiPy within your project, but without using pip or setuptools, just download [the latest version](https://github.com/Kyria/EsiPy/releases/latest) and import it. 

You will also need the following dependencies :
* requests 
* pyswagger
* six 
* pytz
* python-jose

*You can get them from the requirements.txt in the project*
