# -*- coding: utf-8 -*-

"""Non-graphical part of the PyXtal step in a SEAMM flowchart
"""

import logging
from pathlib import Path
import pprint  # noqa: F401
import shutil
import string
import subprocess

from openbabel import openbabel

from chemical_formula import Formula
import pyxtal_step
import seamm
import seamm_util
from seamm_util import ureg, Q_  # noqa: F401
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __

# In addition to the normal logger, two logger-like printing facilities are
# defined: "job" and "printer". "job" send output to the main job.out file for
# the job, and should be used very sparingly, typically to echo what this step
# will do in the initial summary of the job.
#
# "printer" sends output to the file "step.out" in this steps working
# directory, and is used for all normal output from this step.

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("PyXtal")

if "OpenBabel_version" not in globals():
    global OpenBabel_version
    OpenBabel_version = None


class PyXtal(seamm.Node):
    """
    The non-graphical part of a PyXtal step in a flowchart.

    Attributes
    ----------
    parser : configargparse.ArgParser
        The parser object.

    options : tuple
        It contains a two item tuple containing the populated namespace and the
        list of remaining argument strings.

    subflowchart : seamm.Flowchart
        A SEAMM Flowchart object that represents a subflowchart, if needed.

    parameters : PyXtalParameters
        The control parameters for PyXtal.

    See Also
    --------
    TkPyXtal,
    PyXtal, PyXtalParameters
    """

    def __init__(self, flowchart=None, title="PyXtal", extension=None, logger=logger):
        """A step for PyXtal in a SEAMM flowchart.

        You may wish to change the title above, which is the string displayed
        in the box representing the step in the flowchart.

        Parameters
        ----------
        flowchart: seamm.Flowchart
            The non-graphical flowchart that contains this step.

        title: str
            The name displayed in the flowchart.
        extension: None
            Not yet implemented
        logger : Logger = logger
            The logger to use and pass to parent classes

        Returns
        -------
        None
        """
        logger.debug(f"Creating PyXtal {self}")

        super().__init__(
            flowchart=flowchart,
            title="PyXtal",
            extension=extension,
            module=__name__,
            logger=logger,
        )  # yapf: disable

        self.parameters = pyxtal_step.PyXtalParameters()

    @property
    def version(self):
        """The semantic version of this module."""
        return pyxtal_step.__version__

    @property
    def git_revision(self):
        """The git version of this module."""
        return pyxtal_step.__git_revision__

    def create_parser(self):
        """Setup the command-line / config file parser"""
        # parser_name = 'pyxtal-step'
        parser_name = self.step_type
        parser = seamm_util.getParser(name="SEAMM")

        # Remember if the parser exists ... this type of step may have been
        # found before
        parser_exists = parser.exists(parser_name)

        # Create the standard options, e.g. log-level
        result = super().create_parser(name=parser_name)

        if parser_exists:
            return result

        # Options for PyXtal
        parser.add_argument(
            parser_name,
            "--pyxtal-path",
            default="",
            help="the path to the PyXtal executable",
        )

        return result

    def description_text(self, P=None):
        """Create the text description of what this step will do.
        The dictionary of control values is passed in as P so that
        the code can test values, etc.

        Parameters
        ----------
        P: dict
            An optional dictionary of the current values of the control
            parameters.
        Returns
        -------
        str
            A description of the current step.
        """
        if not P:
            P = self.parameters.values_to_dict()

        if "0-D" in P["dimensionality"]:
            text = "Create a molecule "
        elif "1-D" in P["dimensionality"]:
            text = "Create a 1-D rod "
        elif "2-D" in P["dimensionality"]:
            text = "Create a 2-D slab "
        elif "3-D" in P["dimensionality"]:
            text = "Create a 3-D crystal "
        elif self.is_expr(P["dimensionality"]):
            text = (
                "Create a system whose dimensionality is given by "
                f"{P['dimensionality']} "
            )
        else:
            raise ValueError(f"Can't handle dimensionality: {P['dimensionality']}")

        build_type = P["build type"]
        if build_type == "atoms":
            text += f"with a chemical formula {P['formula']} and "
        else:
            text += f"using the {P['n_molecules']} copies of the current molecule "
        text += f"and {P['symmetry']} symmetry."

        attempts = P["attempts"]
        if isinstance(attempts, str) and self.is_expr(attempts):
            text += (
                f" The variable {attempts} will determine how many attempts are made "
                "to generate structures. "
            )
            text += seamm.standard_parameters.multiple_structure_handling_description(P)
        elif attempts == 1:
            text += " "
            text += seamm.standard_parameters.structure_handling_description(P)
        else:
            text += (
                f" PyXtal will make {attempts} attempts to generate structures, "
                "resulting in up to that many conformers. "
            )
            text += seamm.standard_parameters.multiple_structure_handling_description(P)

        return self.header + "\n" + __(text, **P, indent=4 * " ").__str__()

    def run(self):
        """Run a PyXtal step.

        Parameters
        ----------
        None

        Returns
        -------
        seamm.Node
            The next node object in the flowchart.
        """
        global OpenBabel_version

        next_node = super().run(printer)
        # Get the values of the parameters, dereferencing any variables
        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        # Print what we are doing
        printer.important(__(self.description_text(P), indent=self.indent))

        # Get the current configuration and the one to put the new structures in
        system_db = self.get_variable("_system_db")
        current_system = system_db.system
        if current_system is None:
            current_configuration = None
        else:
            current_configuration = current_system.configuration

        system, configuration = self.get_system_configuration(
            P, structure_handling=True
        )

        # Access the options
        options = self.options

        # What files to send to and bring back from PyXtal
        files = {}
        return_files = []

        # Run the calculation
        local = seamm.ExecLocal()
        exe = Path(options["pyxtal_path"]) / "pyxtal_main.py"

        cmd = [str(exe)]

        # Build type: atoms or molecules
        if P["build type"] == "molecules":
            cmd.append("-m")

        # Dimensionality
        cmd.append("-d")
        if "0-D" in P["dimensionality"]:
            cmd.append("0")
            return_files.append("*.xyz")
        elif "1-D" in P["dimensionality"]:
            cmd.append("1")
            cmd.append("-t")
            area = P["area"].to("Å^2").magnitude
            cmd.append(f"{area:f.3}")
            return_files.append("*.cif")
        elif "2-D" in P["dimensionality"]:
            cmd.append("2")
            cmd.append("-t")
            thickness = P["thickness"].to("Å").magnitude
            cmd.append(f"{thickness:f.3}")
            return_files.append("*.cif")
        elif "3-D" in P["dimensionality"]:
            cmd.append("3")
            return_files.append("*.cif")

        # Symmetry
        cmd.append("-s")
        cmd.append(P["symmetry"])

        # Elements or molecules
        cmd.append("-e")
        if P["build type"] == "molecules":
            # Generate an .xyz file of the molecule

            # "Simple" approach using Open Babel doesn't give enough precision
            # obMol = current_configuration.to_OBMol()
            # obMol.SetTitle(f"{current_system.name}/{current_configuration.name}")
            # obConversion = openbabel.OBConversion()
            # obConversion.SetOutFormat("xyz")
            # files["in1.xyz"] = obConversion.WriteString(obMol)

            lines = []
            lines.append(str(current_configuration.n_atoms))
            lines.append(f"{current_system.name}/{current_configuration.name}")
            for symbol, xyz in zip(
                current_configuration.atoms.symbols,
                current_configuration.atoms.coordinates,
            ):
                lines.append(f"{symbol:2} {xyz[0]:15.8f} {xyz[1]:15.8f} {xyz[2]:15.8f}")

            files["in1.xyz"] = "\n".join(lines)

            cmd.append("./in1.xyz")

            cmd.append("-n")
            cmd.append(f"{P['n_molecules']}")
        else:
            f = Formula(P["formula"])
            symbols = [i for i, j in f.to_dict().items()]
            n_atoms = [str(j) for i, j in f.to_dict().items()]

            cmd.append(",".join(symbols))

            # Number of atoms
            cmd.append("-n")
            cmd.append(",".join(n_atoms))

        # Put the output in the current directory
        cmd.append("-o")
        cmd.append(".")

        # And number of attempts
        cmd.append("-a")
        cmd.append(str(P["attempts"]))

        # Write the input files to the current directory
        directory = Path(self.directory)
        directory.mkdir(parents=True, exist_ok=True)
        for filename in files:
            path = directory / filename
            with path.open(mode="w") as fd:
                fd.write(files[filename])

        # Run PyXtal
        result = local.run(cmd, files=files, return_files=return_files)

        if result is None:
            logger.error("There was an error running PyXtal")
            return None

        logger.debug("\n" + pprint.pformat(result))

        logger.info("stdout:\n" + result["stdout"])
        if result["stderr"] != "":
            logger.warning("stderr:\n" + result["stderr"])

        # Write the output files to the current directory
        if "stdout" in result and result["stdout"] != "":
            path = directory / "stdout.txt"
            with path.open(mode="w") as fd:
                fd.write(result["stdout"])

        if result["stderr"] != "":
            self.logger.warning("stderr:\n" + result["stderr"])
            path = directory / "stderr.txt"
            with path.open(mode="w") as fd:
                fd.write(result["stderr"])

        for filename in result["files"]:
            if filename[0] == "@":
                subdir, fname = filename[1:].split("+")
                path = directory / subdir / fname
            else:
                path = directory / filename
            with path.open(mode="w") as fd:
                if result[filename]["data"] is not None:
                    fd.write(result[filename]["data"])
                else:
                    fd.write(result[filename]["exception"])

        # Get the structures
        subsequent_as_configurations = (
            P["subsequent structure handling"] == "Create a new configuration"
        )
        system_name = P["system name"]
        configuration_name = P["configuration name"]

        n_structures = 0
        for filename in result["files"]:
            if "0-D" in P["dimensionality"] and filename.endswith(".xyz"):
                obConversion = openbabel.OBConversion()
                obConversion.SetInAndOutFormats("xyz", "mol")
                obMol = openbabel.OBMol()
                path = directory / filename
                ok = obConversion.ReadFile(obMol, str(path))
                if not ok:
                    raise RuntimeError(f"Error reading {filename}")
            elif filename.endswith(".cif"):
                pass
            else:
                continue

            n_structures += 1
            if n_structures > 1:
                if subsequent_as_configurations:
                    configuration = system.create_configuration()
                else:
                    system = system_db.create_system()
                    configuration = system.create_configuration()

            if "0-D" in P["dimensionality"] and filename.endswith(".xyz"):
                configuration.from_OBMol(obMol)
            elif filename.endswith(".cif"):
                configuration.from_cif_text(result[filename]["data"])

            # Set the system name
            if system_name is not None and system_name != "":
                lower_name = system_name.lower()
                if "from file" in lower_name:
                    system.name = obMol.GetTitle()
                elif "canonical smiles" in lower_name:
                    system.name = configuration.canonical_smiles
                elif "smiles" in lower_name:
                    system.name = configuration.smiles
                else:
                    system.name = system_name

            # And the configuration name
            if configuration_name is not None and configuration_name != "":
                lower_name = configuration_name.lower()
                if "from file" in lower_name:
                    configuration.name = obMol.GetTitle()
                elif "canonical smiles" in lower_name:
                    configuration.name = configuration.canonical_smiles
                elif "smiles" in lower_name:
                    configuration.name = configuration.smiles
                elif lower_name == "sequential":
                    configuration.name = str(n_structures)
                else:
                    configuration.name = configuration_name

        # Add other citations here or in the appropriate place in the code.
        # Add the bibtex to data/references.bib, and add a self.reference.cite
        # similar to the above to actually add the citation to the references.

        self.references.cite(
            raw=self._bibliography["pyxtal"],
            alias="pyxtal_cpc",
            module="pyxtal_step",
            level=1,
            note="The principle PyXtal citation.",
        )

        # get the version of the PyXtal package
        if "stdout" in result and result["stdout"] != "":
            version = None
            for line in result["stdout"].splitlines():
                if "---(version" in line:
                    version = line.split()[1]
                    break
            if version is not None:
                template = string.Template(self._bibliography["pyxtal_exe"])

                citation = template.substitute(version=version)

                self.references.cite(
                    raw=citation,
                    alias="pyxtal-exe",
                    module="pyxtal_step",
                    level=1,
                    note="The principle citation for the PyXtal Python package.",
                )

        # Add the citations for Open Babel
        self.references.cite(
            raw=self._bibliography["openbabel"],
            alias="openbabel_jcinf",
            module="pyxtal_step",
            level=1,
            note="The principle Open Babel citation.",
        )

        # See if we can get the version of obabel
        if OpenBabel_version is None:
            path = shutil.which("obabel")
            if path is not None:
                path = Path(path).expanduser().resolve()
                try:
                    result = subprocess.run(
                        [str(path), "--version"],
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        text=True,
                    )
                except Exception:
                    OpenBabel_version = "unknown"
                else:
                    OpenBabel_version = "unknown"
                    lines = result.stdout.splitlines()
                    for line in lines:
                        line = line.strip()
                        tmp = line.split()
                        if len(tmp) == 9 and tmp[0] == "Open":
                            OpenBabel_version = {
                                "version": tmp[2],
                                "month": tmp[4],
                                "year": tmp[6],
                            }
                        break

        if isinstance(OpenBabel_version, dict):
            try:
                template = string.Template(self._bibliography["obabel"])

                citation = template.substitute(
                    month=OpenBabel_version["month"],
                    version=OpenBabel_version["version"],
                    year=OpenBabel_version["year"],
                )

                self.references.cite(
                    raw=citation,
                    alias="obabel-exe",
                    module="pyxtal_step",
                    level=1,
                    note="The principle citation for the Open Babel executables.",
                )
            except Exception:
                pass

        # Finish the output
        printer.important(
            __(f"\n    Created {n_structures} structures.", indent=4 * " ")
        )
        printer.important("")

        return next_node

    def analyze(self, indent="", **kwargs):
        """Do any analysis of the output from this step.

        Also print important results to the local step.out file using
        "printer".

        Parameters
        ----------
        indent: str
            An extra indentation for the output
        """
        printer.normal(
            __(
                "This is a placeholder for the results from the PyXtal step",
                indent=4 * " ",
                wrap=True,
                dedent=False,
            )
        )
