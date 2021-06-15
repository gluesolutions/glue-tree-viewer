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
    fill = CallbackProperty(False, docstring="show this layer")


class TreeLayerArtist(LayerArtist):

    _layer_state_cls = TreeLayerState

    def __init__(self, fn, session, apply_subset_state, parent, *args, **kwargs):
        self.treeviewer = parent
        super(TreeLayerArtist, self).__init__(*args, **kwargs)
        print("tree layer artist being initialzied")
        self.setCentralWidget = fn
        self.session = session
        self.apply_subset_state = apply_subset_state

        self.state.add_callback("fill", self._on_fill_checked)

    def clear(self):
        print("clear1")

    def remove(self):
        print("remove1")

    def redraw(self):
        pass
        # self.scene.draw()
        # self.view.init_values()

    def update(self):
        print("update1")

    def _on_fill_checked(self, *args):
        print("onf ill checked", args)


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
from glue.core.subset import Subset
from echo import SelectionCallbackProperty
from collections import OrderedDict


NODE_TYPES = OrderedDict(
    [("circle", "Circle"), ("square", "Square"), ("sphere", "Sphere")]
)

SHOW_TEXT = OrderedDict([(True, "Yes"), (False, "No")])


def layout(node):
    node.children.sort(key=lambda n: n.dist + n.get_farthest_leaf()[1], reverse=True)


class TreeViewerState(ViewerState):
    node_att = SelectionCallbackProperty(
        docstring="the node type to display on the tree viewer"
    )
    showtext_att = SelectionCallbackProperty(docstring="to show the text on the tree")

    def __init__(self, *args, **kwargs):
        super(TreeViewerState, self).__init__(*args, **kwargs)

        TreeViewerState.node_att.set_choices(self, list(NODE_TYPES))
        TreeViewerState.node_att.set_display_func(self, NODE_TYPES.get)

        TreeViewerState.showtext_att.set_choices(self, list(SHOW_TEXT))
        TreeViewerState.showtext_att.set_display_func(self, SHOW_TEXT.get)


from glue.utils.qt import load_ui
import os
from echo.qt import autoconnect_callbacks_to_qt


class TreeViewerStateWidget(QWidget):
    def __init__(self, viewer_state=None, session=None):

        super(TreeViewerStateWidget, self).__init__()

        self.ui = load_ui("viewer_state.ui", self, directory=os.path.dirname(__file__))

        self.viewer_state = viewer_state
        self._connections = autoconnect_callbacks_to_qt(self.viewer_state, self.ui)


class TreeDataViewer(DataViewer):
    LABEL = "ete3 based Tree Viewer"

    _state_cls = TreeViewerState
    _options_cls = TreeViewerStateWidget
    _data_artist_cls = TreeLayerArtist
    _subset_artist_cls = TreeLayerArtist

    # tools = ['table:rowselect']

    # additional stuff for qt

    # _layer_style_widget_cls = TutorialLayerStateWidget
    # _options_cls =

    def __init__(self, session, state=None, parent=None, widget=None):
        super(TreeDataViewer, self).__init__(session, state=state, parent=parent)
        self.s = session

        assert isinstance(self.state, ViewerState)
        self.state.add_callback("layers", self._on_layers_changed)

        self.state.add_callback("node_att", self._on_node_change)
        self.state.add_callback("showtext_att", self._on_showtext_change)

        self._on_layers_changed()

        self.default_style = lambda: ete3.NodeStyle()
        self.tree_style = ete3.TreeStyle()
        self.tree_style.layout_fn = layout

        # we do not have data yet
        # self.init_treedrawing(self.state.layer.data)

    def _on_node_change(self, newval, **kwargs):
        print("on node change", newval, kwargs)
        # QUESTION are there just a billion nodestyle classes clogging things up?
        def newstylefn():
            st = ete3.NodeStyle()
            st["shape"] = newval
            return st

        self.default_style = newstylefn
        for node in self.data.tdata.traverse():
            # PERFORMANCE this creates tons of garbage
            node.set_style(newstylefn())
            # TODO will not last after layers update
        self.redraw()

    def _on_showtext_change(self, newval, **kwargs):
        self.tree_style.show_leaf_name = newval
        self.init_treedrawing(self.data)

    def add_data(self, data):
        assert hasattr(data, "tdata")

        self.init_treedrawing(data)
        return super(TreeDataViewer, self).add_data(data)

    # def add_subset(self, subset):
    # print('adding subset')
    ##if subset.data != self.data:
    ##raise ValueError("subset parent data does not match existing tree data")
    # return super(TreeDataViewer, self).add_subset(subset)

    def _on_layers_changed(self, *args):
        from collections import defaultdict

        self.title2color = defaultdict((lambda: "#FFFFFF"))
        print("layers changed")
        for layerstate in self.layers:
            print("layerstate", layerstate)
            layer = layerstate.layer
            if isinstance(layer, Subset):
                if "Subset" in layerstate.__str__():
                    pass
                    # import pdb
                    # pdb.set_trace()
                print("subset_mask")
                print(layer.to_mask())
                print("longlen", len(layer.data["tree nodes"]))
                print("shortlen", len(layer.data["tree nodes"][layer.to_mask()]))
                goodnames = layer.data["tree nodes"][layer.to_mask()]
                for name in goodnames:
                    # TODO add color blending
                    if layerstate.visible:
                        self.title2color[name] = layer.style.color
                    else:
                        print("uh")
                        self.title2color[name] = "#FFFFFF"

                # { make code to tree node conversion }
                print("found subset")

                for node in layer.data.tdata.traverse():
                    print("node.title", node.name)
                    st = self.default_style()
                    color = self.title2color[node.name]
                    st["bgcolor"] = color
                    node.set_style(st)

                # redraw
                self.redraw()
            else:
                assert hasattr(layer, "tdata")

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        assert cls == TreeLayerArtist
        return cls(
            self.setCentralWidget,
            self.s,
            self.apply_subset_state,
            self,
            self.state,
            layer=layer,
            layer_state=layer_state,
        )

    def init_treedrawing(self, data):
        self.data = data
        t = self.data.tdata

        # do qt stuff {

        # show_tree stuff {

        scene, ts = _TreeScene(), self.tree_style

        # set style of nodes appropirate to sublcasses

        self.scene = scene

        tree_item, n2i, n2f = render(t, ts)
        scene.init_values(t, ts, n2i, n2f)

        tree_item.setParentItem(scene.master_item)
        scene.addItem(scene.master_item)

        # }

        # _GUI class stuff {

        self.scene.GUI = self
        self.view = _TreeView(
            self.session, self.data, self.apply_subset_state, self.scene
        )
        self.scene.view = self.view
        self.node_properties = None
        self.view.prop_table = None

        # }

        self.setCentralWidget(self.view)

        self.redraw()

        return True

    def redraw(self):
        self.scene.draw()
        self.view.init_values()


from glue.config import qt_client

qt_client.add(TreeDataViewer)


# @menubar_plugin("link data on key")
# def my_plugin(sesssion, data_collection):
# print('buttin')
# return


# BUG: we can't save the session

# how to send links from tree viewer

# PERFORMANCE:  only do collision checks when the selection line changes, not every frame.

# TODO
# press enter to submit subset
# https://github.com/glue-viz/glue/blob/241edb32ab6f4a82adf02ef3711c16342fd214ed/glue/viewers/table/qt/data_viewer.py#L251
# display subsets on tree

# TODO use https://github.com/glue-viz/glue/blob/241edb32ab6f4a82adf02ef3711c16342fd214ed/glue/utils/array.py#L497 this class to represent trees?

# TODO make it listen to hub messages nicely
# TODO click AND drag options
