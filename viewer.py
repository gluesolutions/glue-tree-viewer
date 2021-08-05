# this file based on http://docs.glueviz.org/en/stable/customizing_guide/viewer.html


# -- VIEWER STATE CLASS
from glue.viewers.common.state import ViewerState
from glue.external.echo import CallbackProperty
from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.config import viewer_tool
from glue.viewers.common.tool import CheckableTool, Tool

from collections import defaultdict

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

from glue.utils.colors import alpha_blend_colors
from glue.utils.qt import mpl_to_qt_color

def full_equal(dfd1, dfd2):
    if dfd1 == dfd2:
        return True

    allkeys = set(dfd1.keys()).union(set(dfd2.keys()))

    return all(dfd1[k] == dfd2[k] for k in allkeys)


a = defaultdict(int)
b = defaultdict(int)

a["key"] = 0

assert a != b
assert full_equal(a, b)


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
        self.treeviewer.redraw()

    def remove(self):
        print("remove1")
        #self.treeviewer.redraw()

    def redraw(self):
        print("redraw1")
        # self.scene.draw()
        # self.view.init_values()
        self.treeviewer.redraw()

    def update(self):
        # this happens when the subset is changed, but also other places.
        print("layer updated, redrawing")
        self.treeviewer.redraw()

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
from glue.core.message import LayerArtistUpdatedMessage, LayerArtistVisibilityMessage


class TreeViewerStateWidget(QWidget):
    def __init__(self, viewer_state=None, session=None):

        super(TreeViewerStateWidget, self).__init__()

        self.ui = load_ui("viewer_state.ui", self, directory=os.path.dirname(__file__))

        self.viewer_state = viewer_state
        self._connections = autoconnect_callbacks_to_qt(self.viewer_state, self.ui)


from glue.viewers.common.qt.toolbar import BasicToolbar
import traceback


class TreeDataViewer(DataViewer):
    LABEL = "ete3 based Tree Viewer"

    _state_cls = TreeViewerState
    _options_cls = TreeViewerStateWidget
    _data_artist_cls = TreeLayerArtist
    _subset_artist_cls = TreeLayerArtist

    _toolbar_cls = BasicToolbar
    tools = ["tree:home", "tree:pan", "tree:rectzoom", "tree:lineselect"]

    # additional stuff for qt

    # _layer_style_widget_cls = TutorialLayerStateWidget
    # _options_cls =

    def __init__(self, session, state=None, parent=None, widget=None):
        super(TreeDataViewer, self).__init__(session, state=state, parent=parent)
        self.s = session

        # TODO move these to treeviewerstate?
        print('cache born, reset to epmty')
        self.CACHED_title2color = defaultdict((lambda: []))

        assert isinstance(self.state, ViewerState)
        self.state.add_global_callback(self._on_layers_changed)

        self.state.add_callback("node_att", self._on_node_change)
        self.state.add_callback("showtext_att", self._on_showtext_change)

        self.default_style = lambda: ete3.NodeStyle()
        self.tree_style = ete3.TreeStyle()
        self.tree_style.layout_fn = layout

        self._on_layers_changed(None)


    def register_to_hub(self, hub):
        super(TreeDataViewer, self).register_to_hub(hub)
        print("registering to hub")

        # hub.subscribe(self, LayerArtistUpdatedMessage, handler = self._on_layers_changed)
        # hub.subscribe(self, LayerArtistVisibilityMessage, handler = self._on_layers_changed)

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
        #self.redraw()

    def add_data(self, data):
        assert hasattr(data, "tdata")

        for node in data.tdata.traverse():
            st = self.default_style()
            node.set_style(st)

        self.init_treedrawing(data)
        return super(TreeDataViewer, self).add_data(data)

    def get_title2color(self):
        self.title2color = defaultdict((lambda: []))

        for layer_artist in self.layers:
            print("layerstate", layer_artist)
            layer = layer_artist.layer
            if isinstance(layer, Subset):
                # print("subset_mask")
                # PROBLEM: why does this return all false until its refreshed..
                # print(layer.to_mask())
                # print("longlen", len(layer.data["tree nodes"]))
                # print("shortlen", len(layer.data["tree nodes"][layer.to_mask()]))
                cid = layer.data.tree_component_id
                from glue.core.exceptions import IncompatibleAttribute

                try:
                    goodnames = layer.data[cid][layer.to_mask()]
                except IncompatibleAttribute as exc:
                    if layer_artist.enabled:
                        layer_artist.disable_incompatible_subset()
                else:
                    for name in goodnames:
                        if layer_artist.visible:
                            self.title2color[name].append(layer.style.color)
                        else:
                            colorlist = self.title2color[name]
                            if layer.style.color in colorlist:
                                # this modifies the dict..
                                colorlist.remove(layer.style.color)

            else:
                assert hasattr(layer, "tdata")

    def _on_layers_changed(self, *args, **kwargs):
        # make sure it only tries to draw when it
        if hasattr(self, "scene"):
            self.redraw()
        else:
            print("scene not loaded yet")

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

        self.scene.draw()
        self.view.init_values()

        return True

    def redraw(self):
        print('redrawing')

        self.get_title2color()

        if full_equal(self.CACHED_title2color, self.title2color):
            print("cache: drawing information not changed, not redrawing")
            return

        print("cache: ACTUALLY REDRAWING !!!!")
        self.CACHED_title2color = self.title2color

        for node in self.data.tdata.traverse():
            st = self.default_style()
            nn = node.idx
            colors = self.title2color[nn]

            if colors:
                # performance: we can skip the colors conversion if only one color
                st["bgcolor"] = mpl_to_qt_color(
                    alpha_blend_colors(colors, additional_alpha=0.5)
                ).name()
            else:
                st["bgcolor"] = "#FFFFFF"

            node.set_style(st)

        self.scene.draw()

        # TODO: can we get rid of init_values here?
        self.view.init_values()

    def zoomOut(self):
        from qtpy.QtCore import Qt

        # from https://github.com/etetoolkit/ete/blob/1f587a315f3c61140e3bdbe697e3e86eda6d2eca/ete3/treeview/qt4_gui.py#L231
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def zoomHome(self):
        from qtpy import QtCore
        from qtpy.QtCore import Qt

        # from https://github.com/etetoolkit/ete/blob/1f587a315f3c61140e3bdbe697e3e86eda6d2eca/ete3/treeview/qt4_gui.py#L231
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def remove(self):
        print("remove2")


@viewer_tool
class HomeButton(Tool):

    icon = "glue_home"
    tool_id = "tree:home"
    action_text = "Navigates camera to look at root node"
    tool_tip = "View tree root"
    shortcut = "H"

    def __init__(self, viewer):
        super(HomeButton, self).__init__(viewer)

    def activate(self):
        self.viewer.zoomHome()

    def close(self):
        pass


DEFUALT_MOUSE_MODE = "none"


@viewer_tool
class ZoomOut(CheckableTool):

    icon = "glue_zoom_to_rect"
    tool_id = "tree:rectzoom"
    action_text = "Zooms camera to rect selection"
    tool_tip = "View tree root"
    shortcut = "Z"

    def __init__(self, viewer):
        super(ZoomOut, self).__init__(viewer)

    def activate(self):
        self.viewer.view.zoomrect.setActive(False)
        self.viewer.view.zoomrect.setVisible(False)

        self.viewer.view.mouseMode = "rectzoom"

    def deactivate(self):
        self.viewer.view.zoomrect.setActive(False)
        self.viewer.view.zoomrect.setVisible(False)

        self.viewer.view.mouseMode = DEFUALT_MOUSE_MODE

    def close(self):
        pass


@viewer_tool
class LineSelect(CheckableTool):

    icon = "glue_row_select"
    tool_id = "tree:lineselect"
    action_text = "select nodes using a collision line"
    tool_tip = "draw line to select"
    shortcut = "L"

    def __init__(self, viewer):
        super(CheckableTool, self).__init__(viewer)

    def activate(self):
        self.viewer.view.mouseMode = "lineselect"

    def deactivate(self):

        self.viewer.view.selector.setActive(False)
        self.viewer.view.selector.clear_cache()

        # setvisible(false)?
        self.viewer.view.mouseMode = DEFUALT_MOUSE_MODE
        # go through and unhighlight_node every node

    def close(self):
        pass


@viewer_tool
class PanTool(CheckableTool):

    icon = "glue_move"
    tool_id = "tree:pan"
    action_text = "Pan view of tree with mouse"
    tool_tip = "Pan view of tree with mouse"
    shortcut = "M"

    def __init__(self, viewer):
        super(PanTool, self).__init__(viewer)

    def activate(self):
        self.viewer.view.mouseMode = "pan"

    def deactivate(self):
        self.viewer.view.mouseMode = DEFUALT_MOUSE_MODE

    def close(self):
        pass



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

# BUG sometimes it gets completely red and wont delete, even after I close it(i think its a static variable being changed, probably a root node getting selected)
