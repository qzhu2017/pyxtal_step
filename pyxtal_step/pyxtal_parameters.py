# -*- coding: utf-8 -*-
"""
Control parameters for the PyXtal step in a SEAMM flowchart
"""

import logging
import seamm
import pprint  # noqa: F401

logger = logging.getLogger(__name__)


class PyXtalParameters(seamm.Parameters):
    """
    The control parameters for PyXtal.

    The developer will add a dictionary of Parameters to this class.
    The keys are parameters for the current plugin, which themselves
    might be dictionaries.

    You need to replace the "time" example below with one or more
    definitions of the control parameters for your plugin and application.

    Attributes
    ----------
    parameters : {"kind", "default", "default_units", "enumeration",
                  "format_string", description", help_text"}
        A dictionary containing the parameters for the current step.
        Each key of the dictionary is a dictionary that contains the
        the following keys: kind, default, default_units, enumeration,
        format_string, description and help text.

    parameters["kind"]: custom
        Specifies the kind of a variable. While the "kind" of a variable might
        be a numeric value, it may still have enumerated custom values
        meaningful to the user. For instance, if the parameter is
        a convergence criterion for an optimizer, custom values like "normal",
        "precise", etc, might be adequate. In addition, any
        parameter can be set to a variable of expression, indicated by having
        "$" as the first character in the field. For example, $OPTIMIZER_CONV.

    parameters["default"] : "integer" or "float" or "string" or "boolean" or
        "enum" The default value of the parameter, used to reset it.

    parameters["default_units"] : str
        The default units, used for resetting the value.

    parameters["enumeration"]: tuple
        A tuple of enumerated values.

    parameters["format_string"]: str
        A format string for "pretty" output.

    parameters["description"]: str
        A short string used as a prompt in the GUI.

    parameters["help_text"]: tuple
        A longer string to display as help for the user.

    See Also
    --------
    PyXtal, TkPyXtal, PyXtal
    PyXtalParameters, PyXtalStep

    Examples
    --------
    parameters = {
        "time": {
            "default": 100.0,
            "kind": "float",
            "default_units": "ps",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Simulation time:",
            "help_text": ("The time to simulate in the dynamics run.")
        },
    }
    """

    parameters = {
        "build type": {
            "default": "atoms",
            "kind": "enum",
            "default_units": None,
            "enumeration": (
                "atoms",
                "molecules",
            ),
            "format_string": "",
            "description": "Build using:",
            "help_text": (
                "Whether to use atoms of molecules as the basic building block."
            ),
        },
        "dimensionality": {
            "default": "3-D crystal",
            "kind": "enum",
            "default_units": None,
            "enumeration": (
                "0-D molecular",
                "1-D rod",
                "2-D layer",
                "3-D crystal",
            ),
            "format_string": "",
            "description": "Dimensionality:",
            "help_text": (
                "Whether the desired system is molecular, a rod, layer or 3-D crystal"
            ),
        },
        "symmetry": {
            "default": "",
            "kind": "enum",
            "default_units": None,
            "enumeration": tuple(),
            "format_string": "",
            "description": "Symmetry:",
            "help_text": (
                "The symmetry -- point, rod, layer, or space group -- for the system."
            ),
        },
        "formula": {
            "default": "",
            "kind": "string",
            "default_units": None,
            "enumeration": tuple(),
            "format_string": "",
            "description": "Formula:",
            "help_text": "The chemical formula for the molecule or crystal.",
        },
        "n_molecules": {
            "default": 1,
            "kind": "integer",
            "default_units": None,
            "enumeration": tuple(),
            "format_string": "",
            "description": "Number of molecules:",
            "help_text": "The number of molecules in the final structure.",
        },
        "attempts": {
            "default": 1,
            "kind": "integer",
            "default_units": None,
            "enumeration": tuple(),
            "format_string": "",
            "description": "Number of attempts:",
            "help_text": (
                "The number of time to try making the structure. "
                "The number of structures actually generated may be less than this."
            ),
        },
        "thickness": {
            "default": 5.0,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": "%.2f",
            "description": "Slab thickness:",
            "help_text": "The thickness of the generated slab.",
        },
        "area": {
            "default": 25.0,
            "kind": "float",
            "default_units": "Å^2",
            "enumeration": tuple(),
            "format_string": "%.2f",
            "description": "Cross-sectional area:",
            "help_text": "The area of the cross section of the rod.",
        },
    }

    def __init__(self, defaults={}, data=None):
        """
        Initialize the parameters, by default with the parameters defined above

        Parameters
        ----------
        defaults: dict
            A dictionary of parameters to initialize. The parameters
            above are used first and any given will override/add to them.
        data: dict
            A dictionary of keys and a subdictionary with value and units
            for updating the current, default values.

        Returns
        -------
        None
        """

        logger.debug("PyXtalParameters.__init__")

        super().__init__(
            defaults={
                **PyXtalParameters.parameters,
                **seamm.standard_parameters.structure_handling_parameters,
                **defaults,
            },
            data=data,
        )
