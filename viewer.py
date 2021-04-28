# this file based on http://docs.glueviz.org/en/stable/customizing_guide/viewer.html


# -- VIEWER STATE CLASS
from glue.viewers.common.state import ViewerState
from glue.external.echo import CallbackProperty
from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.config import viewer_tool


from ete3.treeview.qt4_render import (
    _TreeScene,
    render,
    get_tree_img_map,
    init_tree_style,
)
from qt4_gui_modified import _TreeView

import ete3

# -- LAYER STATE
from glue.viewers.common.state import LayerState

from glue.viewers.common.layer_artist import LayerArtist


class TreeLayerState(LayerState):
    fill = CallbackProperty(False, docstring='show this layer')


class TreeLayerArtist(LayerArtist):

    _layer_state_cls = TreeLayerState

    def __init__(self, axes, *args, **kwargs):
        print("args", args)
        print("kwargs", kwargs)
        # del kwargs['layer_state'] # BUG
        print("thingsi have", self.__dir__)
        super(TreeLayerArtist, self).__init__(*args, **kwargs)

        self.state.add_callback('fill', self._on_fill_checked)

    def clear(self):
        print("clear1")

    def remove(self):
        print("remove1")

    def redraw(self):
        print("redraw1")

    def update(self):
        print("update1")

    def _on_fill_checked(self, *args):
        print('onf ill checked', args)


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


# -- FINAL: DATA VIEWER CLASS
from glue.viewers.common.qt.data_viewer import DataViewer
from matplotlib import pyplot as plt


class TreeViewerState(ViewerState):
    pass

class TreeDataViewer(DataViewer):
    LABEL = "ete3 based Tree Viewer"

    _state_cls = TreeViewerState
    _data_artist_cls = TreeLayerArtist
    _subset_artist_cls = TreeLayerArtist

    #tools = ['table:rowselect']

    # additional stuff for qt

    #_layer_style_widget_cls = TutorialLayerStateWidget
    #_options_cls = 

    def __init__(self, session, state=None, parent=None, widget=None):
        super(TreeDataViewer, self).__init__(session, state=state, parent=parent)

        self.tdata = None

        assert isinstance(self.state, ViewerState)
        self.state.add_callback('layers', self._on_layers_changed)
        self._on_layers_changed()

    def _on_layers_changed(self, *args):
        for layerstate in self.state.layers:
            print('layerstate', layerstate)

        print('layers chagned')

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        # QUESTION: also, where does self.state come from? guess: from superclass, Viewer, and is an instantiation of TreeViewerState
        return cls(self.axes, self.state, layer=layer, layer_state=layer_state)
    
    def _redraw(self):
        import pdb;
        pdb.set_trace()
        self.scene.draw()
        self.view.init_values()

    def add_data(self, data):
        self.data = data
        t = self.data.tdata


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

        # get the x/y positions of tree segments {
        # maybe call init_node_dimensions (qt4_render.py:1031)
        # or assume its already called
        # {lets just scrap this and modify their actual gui class}
        # but we might give up, then try to use their init_node_dimensions values anyway
        
        # }


        # QUESTION: should we use show_tree code drawer.py:73,
                        # {POSA}. we are already doing this and it almost works
        #        or should we use gui class qt4_gui:133

        self.setCentralWidget(self.view)

        self._redraw()

        return True


from glue.config import qt_client

qt_client.add(TreeDataViewer)

# BUG: we can't save the session
# FEATURE: one of the sliders controlls which cutoff the dendrogram code uses?
#     (wont work for general tree class, just dendrograms...)

# how to send links from tree viewer
# https://github.com/glue-viz/glue/blob/241edb32ab6f4a82adf02ef3711c16342fd214ed/glue/viewers/table/qt/data_viewer.py#L251
