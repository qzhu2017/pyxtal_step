# -*- coding: utf-8 -*-

"""
pyxtal_step
A SEAMM plug-in for PyXtal
"""

# Bring up the classes so that they appear to be directly in
# the pyxtal_step package.

from pyxtal_step.pyxtal import PyXtal  # noqa: F401
from pyxtal_step.pyxtal_parameters import PyXtalParameters  # noqa: F401
from pyxtal_step.pyxtal_step import PyXtalStep  # noqa: F401
from pyxtal_step.tk_pyxtal import TkPyXtal  # noqa: F401
from pyxtal_step.metadata import (  # noqa: F401
    point_groups,
    rod_groups,
    layer_groups,
    space_groups,
)

# Handle versioneer
from ._version import get_versions

__author__ = "Paul Saxe"
__email__ = "psaxe@vt.edu"
versions = get_versions()
__version__ = versions["version"]
__git_revision__ = versions["full-revisionid"]
del get_versions, versions
