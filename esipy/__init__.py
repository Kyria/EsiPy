# -*- encoding: utf-8 -*-
""" Entry point of EsiPy, also contains shortcuts for all required objects """
from __future__ import absolute_import

try:
    from .client import EsiClient  # noqa
    from .security import EsiSecurity  # noqa
    from .app import EsiApp  # noqa
    from pyswagger import App  # noqa
except ImportError:  # pragma: no cover
            # Not installed or in install (not yet installed) so ignore
    pass

__version__ = '0.5.0'
