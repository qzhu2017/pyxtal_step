# -*- coding: utf-8 -*-

"""The graphical part of a PyXtal step"""

import pprint  # noqa: F401
import tkinter as tk
import tkinter.ttk as ttk

import pyxtal_step
import seamm
from seamm_util import ureg, Q_, units_class  # noqa: F401
import seamm_widgets as sw


class TkPyXtal(seamm.TkNode):
    """
    The graphical part of a PyXtal step in a flowchart.

    Attributes
    ----------
    tk_flowchart : TkFlowchart = None
        The flowchart that we belong to.
    node : Node = None
        The corresponding node of the non-graphical flowchart
    namespace : str
        The namespace of the current step.
    tk_subflowchart : TkFlowchart
        A graphical Flowchart representing a subflowchart
    canvas: tkCanvas = None
        The Tk Canvas to draw on
    dialog : Dialog
        The Pmw dialog object
    x : int = None
        The x-coordinate of the center of the picture of the node
    y : int = None
        The y-coordinate of the center of the picture of the node
    w : int = 200
        The width in pixels of the picture of the node
    h : int = 50
        The height in pixels of the picture of the node
    self[widget] : dict
        A dictionary of tk widgets built using the information
        contained in PyXtal_parameters.py

    See Also
    --------
    PyXtal, TkPyXtal,
    PyXtalParameters,
    """

    def __init__(
        self,
        tk_flowchart=None,
        node=None,
        canvas=None,
        x=None,
        y=None,
        w=200,
        h=50,
    ):
        """
        Initialize a graphical node.

        Parameters
        ----------
        tk_flowchart: Tk_Flowchart
            The graphical flowchart that we are in.
        node: Node
            The non-graphical node for this step.
        namespace: str
            The stevedore namespace for finding sub-nodes.
        canvas: Canvas
           The Tk canvas to draw on.
        x: float
            The x position of the nodes center on the canvas.
        y: float
            The y position of the nodes cetner on the canvas.
        w: float
            The nodes graphical width, in pixels.
        h: float
            The nodes graphical height, in pixels.

        Returns
        -------
        None
        """
        self.dialog = None

        super().__init__(
            tk_flowchart=tk_flowchart,
            node=node,
            canvas=canvas,
            x=x,
            y=y,
            w=w,
            h=h,
        )

    def create_dialog(self):
        """
        Create the dialog. A set of widgets will be chosen by default
        based on what is specified in the PyXtal_parameters
        module.

        Parameters
        ----------
        None

        Returns
        -------
        None

        See Also
        --------
        TkPyXtal.reset_dialog
        """

        frame = super().create_dialog(title="PyXtal")

        # Create two frames, one for the PyXtal parameters and one for where to put the
        # structure.
        frame1 = self["pyxtal frame"] = ttk.LabelFrame(
            frame,
            borderwidth=4,
            relief="sunken",
            text="Structure definition",
            labelanchor="n",
            padding=10,
        )
        frame2 = self["handling frame"] = ttk.LabelFrame(
            frame,
            borderwidth=4,
            relief="sunken",
            text="How to handle the structure",
            labelanchor="n",
            padding=10,
        )

        # Then create the widgets
        P = self.node.parameters
        for key in (
            "build type",
            "dimensionality",
            "symmetry",
            "formula",
            "n_molecules",
            "attempts",
            "thickness",
            "area",
        ):
            self[key] = P[key].widget(frame1)

        for key in (
            "structure handling",
            "subsequent structure handling",
            "system name",
            "configuration name",
        ):
            self[key] = P[key].widget(frame2)

        # Set bindings
        for name in ("build type", "dimensionality", "attempts"):
            combobox = self[name].combobox
            combobox.bind("<<ComboboxSelected>>", self.reset_dialog)
            combobox.bind("<Return>", self.reset_dialog)
            combobox.bind("<FocusOut>", self.reset_dialog)

        # Put in the widgets that are always present
        frame1.grid(row=0, sticky=tk.EW)
        frame2.grid(row=1, sticky=tk.EW)

        frame.columnconfigure(0, weight=1)

        # and lay them out
        self.reset_dialog()

    def reset_dialog(self, widget=None):
        """Layout the widgets in the dialog.

        The widgets are chosen by default from the information in
        PyXtal_parameter.

        This function simply lays them out row by row with
        aligned labels. You may wish a more complicated layout that
        is controlled by values of some of the control parameters.
        If so, edit or override this method

        Parameters
        ----------
        widget : Tk Widget = None

        Returns
        -------
        None

        See Also
        --------
        TkPyXtal.create_dialog
        """
        ##########################
        # Handle the first frame #
        ##########################

        # Remove any widgets previously packed
        frame1 = self["pyxtal frame"]
        for slave in frame1.grid_slaves():
            slave.grid_forget()

        # Set the contents of the symmetry pulldowns for the dimensionality

        build_type = self["build type"].get()
        dimensionality = self["dimensionality"].get()
        symmetry = self["symmetry"].get()

        if build_type == "atoms":
            items = ["build type", "dimensionality", "symmetry", "formula", "attempts"]
        else:
            items = [
                "build type",
                "dimensionality",
                "symmetry",
                "n_molecules",
                "attempts",
            ]

        if "0-D" in dimensionality:
            groups = pyxtal_step.point_groups
        elif "1-D" in dimensionality:
            groups = pyxtal_step.rod_groups
            items.append("area")
        elif "2-D" in dimensionality:
            groups = pyxtal_step.space_groups
            items.append("thickness")
        elif "3-D" in dimensionality:
            groups = pyxtal_step.space_groups
        self["symmetry"].combobox.config(values=groups)
        if symmetry in groups:
            self["symmetry"].set(symmetry)
        else:
            self["symmetry"].set(groups[0])

        # keep track of the row in a variable, so that the layout is flexible
        # if e.g. rows are skipped to control such as "method" here
        row = 0
        widgets = []
        for key in items:
            self[key].grid(row=row, column=0, sticky=tk.EW)
            widgets.append(self[key])
            row += 1

        # Align the labels
        sw.align_labels(widgets)

        # Set the widths and expansion
        frame1.columnconfigure(0, weight=1)

        ###############################
        # Now handle the second frame #
        ###############################

        # Remove any widgets previously packed
        frame2 = self["handling frame"]
        for slave in frame2.grid_slaves():
            slave.grid_forget()

        # Grid the needed widgets
        if self["attempts"].get() == "1":
            items = ("structure handling", "system name", "configuration name")
        else:
            items = (
                "structure handling",
                "subsequent structure handling",
                "system name",
                "configuration name",
            )

        widgets = []
        row = 0
        for item in items:
            self[item].grid(row=row, sticky=tk.EW)
            widgets.append(self[item])
            row += 1
        frame2.columnconfigure(0, weight=1)
        sw.align_labels(widgets)

    def right_click(self, event):
        """
        Handles the right click event on the node.

        Parameters
        ----------
        event : Tk Event

        Returns
        -------
        None

        See Also
        --------
        TkPyXtal.edit
        """

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def handle_help(self):
        """Shows the help to the user when click on help button.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        print("Help not implemented yet for PyXtal!")
