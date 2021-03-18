# this file based on http://docs.glueviz.org/en/stable/customizing_guide/viewer.html


# -- VIEWER STATE CLASS
from glue.viewers.common.state import ViewerState
from glue.external.echo import CallbackProperty
from glue.core.data_combo_helper import ComponentIDComboHelper

from ete3.treeview.qt4_render import (
    _TreeScene,
    render,
    get_tree_img_map,
    init_tree_style,
)
from ete3.treeview.qt4_gui import _TreeView

import ete3


class TreeViewerState(ViewerState):
    _delayed_properties = []
    _ignored_properties = []
    _global_callbacks = []

    scale_att = CallbackProperty(False)

    def scale_att_callback(self, value):
        print("new scale value is ", value)

    def __init__(self, *args, **kwargs):
        # QUESTION: sometimes `, self` is required in super call, sometimes not
        super(TreeViewerState).__init__(*args, **kwargs)
        self.add_callback("scale_att", self.scale_att_callback)
        # self._scale_att_helper = ComponentIDComboHelper(self, 'scale_att')
        print("added callback")


# -- LAYER STATE
from glue.viewers.common.state import LayerState


class TreeLayerState(LayerState):
    # not sure what layers mean in tree context yet
    # maybe this will include just drawing parameters like node size, node glyph settings, branch label, etc
    fill = CallbackProperty(False, docstring="Draw the glyphs of nodes in tree")


from glue.viewers.common.layer_artist import LayerArtist


class TreeLayerArtist(LayerArtist):
    _layer_state_cls = TreeLayerState

    def __init__(self, axes, *args, **kwargs):
        print("args", args)
        print("kwargs", kwargs)
        # del kwargs['layer_state'] # BUG
        print("thingsi have", self.__dir__)
        super(TreeLayerArtist, self).__init__(*args, **kwargs)

    def clear(self):
        print("clear1")

    def remove(self):
        print("remove1")

    def redraw(self):
        print("redraw1")

    def update(self):
        print("update1")


# -- QT special widgets
# --- LayerStateWidget

from glue.external.echo.qt import connect_checkable_button, connect_value
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QGraphicsScene,
    QGraphicsView,
    QSlider,
    QLabel,
)


class TreeLayerStateWidget(QWidget):
    def __init__(self, layer_artist):
        # QUESTION: why is LayerEditWidget different from QWidget ??
        super(TreeLayerStateWidget, self).__init__()

        # TODO: reconcile this with above class which had scale option
        self.checkbox = QCheckBox()

        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        self.setLayout(layout)

        self.layer_state = layer_artist.state
        connect_checkable_button(self.layer_state, "fill", self.checkbox)


# --- ViewerStateWidget
class TreeViewerStateWidget(QWidget):
    def __init__(self, viewer_state, session=None):
        super(TreeViewerStateWidget, self).__init__()

        # viewer state has no callbacks/properties yet, only layer state
        # so we just have empty layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.checkbox = QCheckBox("sstst")
        # self.checkbox.setMinimum(0)
        # self.checkbox.setMaximum(100.0)
        layout.addWidget(QLabel("thickness of lines"))
        layout.addWidget(self.checkbox)

        self.viewer_state = viewer_state
        print("viewer_state", viewer_state)
        print("viewer_statetype", dir(viewer_state))
        viewer_state.scale_att = True

        c1 = connect_checkable_button(self.viewer_state, "scale_att", self.checkbox)
        self.checkbox.setChecked(True)
        assert self.viewer_state.scale_att

        self.checkbox.setChecked(False)
        assert not self.viewer_state.scale_att

        self.viewer_state.scale_att = True
        assert self.checkbox.isChecked()

        self.viewer_state.scale_att = False
        assert not self.checkbox.isChecked()

        print("connected")


# -- FINAL: DATA VIEWER CLASS
from glue.viewers.common.qt.data_viewer import DataViewer
from matplotlib import pyplot as plt


class TreeDataViewer(DataViewer):
    LABEL = "ete3 based Tree Viewer"
    _state_cls = TreeViewerState

    _options_cls = TreeViewerStateWidget
    _layer_style_widget_cls = TreeLayerStateWidget

    _data_artist_cls = TreeLayerArtist
    _subset_artist_cls = TreeLayerArtist

    # additional stuff for qt

    def __init__(self, *args, **kwargs):
        super(TreeDataViewer, self).__init__(*args, **kwargs)
        self.axes = plt.subplot(1, 1, 1)

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        # QUESTION: also, where does self.state come from? guess: from superclass, Viewer, and is an instantiation of TreeViewerState
        return cls(self.axes, self.state, layer=layer, layer_state=layer_state)
    
    def _redraw(self):
        self.scene.draw()
        self.view.init_values()

    def add_data(self, data):
        self.data = data
        t = self.data.get_ete_tree()

        # do qt stuff {

        # show_tree stuff {

        scene, ts = _TreeScene(), ete3.TreeStyle()
        self.scene = scene

        tree_item, n2i, n2f = render(t, ts)
        scene.init_values(t, ts, n2i, n2f)

        tree_item.setParentItem(scene.master_item)
        scene.addItem(scene.master_item)

        # }

        # _GUI class stuff {

        self.scene.GUI = self
        self.view = _TreeView(self.scene)
        self.scene.view = self.view
        self.node_properties = None
        self.view.prop_table = None

        # }


        # QUESTION: should we use show_tree code drawer.py:73,
                        # {POSA}. we are already doing this and it almost works
        #        or should we use gui class qt4_gui:133

        self.setCentralWidget(self.view)

        self._redraw()

        return True


# QUESTION: how to make tree data choose this viewer automatically (is it in viewer code or data code)
# PROBLEM: does not recognize .nw files as treedata, only works if you choose newick file in dropdown

from glue.config import qt_client

qt_client.add(TreeDataViewer)

# BUG: we can't save the session
# FEATURE: one of the sliders controlls which cutoff the dendrogram code uses?
#     (wont work for general tree class, just dendrograms...)
