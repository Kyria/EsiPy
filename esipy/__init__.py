# -*- encoding: utf-8 -*-
from __future__ import absolute_import

try:
    from .client import EsiClient  # noqa
    from .security import EsiSecurity  # noqa
    from pyswagger import App  # noqa
except Exception:  # pragma: no cover
    # Not installed or in install (not yet installed) so ignore
    pass


__version__ = '0.1.1'
