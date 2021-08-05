# this file based on http://docs.glueviz.org/en/stable/customizing_guide/viewer.html

import builtins
import my_actions


# import hack because I need to repalce a class imported by ete3
old_import = builtins.__import__
def temp_import(*args, **kwargs):
    module = old_import(*args, **kwargs)

    if args[0] == 'node_gui_actions':
        module._NodeActions = my_actions.T_NodeActions
    return module

builtins.__import__ = temp_import

from ete3.treeview.qt4_render import (
    _TreeScene,
    render,
    get_tree_img_map,
    init_tree_style,
)

builtins.__import__ = old_import
    

# -- VIEWER STATE CLASS
from glue.viewers.common.state import ViewerState
from glue.external.echo import CallbackProperty
from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.config import viewer_tool
from glue.viewers.common.tool import CheckableTool, Tool

from collections import defaultdict

from qt4_gui_modified import _TreeView

import ete3

# -- LAYER STATE
from glue.viewers.common.state import LayerState

from glue.viewers.common.layer_artist import LayerArtist

from glue.utils.colors import alpha_blend_colors
from glue.utils.qt import mpl_to_qt_color
from qtpy.QtCore import Qt

import numpy as np
from glue.core.subset import CategorySubsetState

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

    def __init__(self, apply_subset_state, parent, *args, **kwargs):
        self.treeviewer = parent
        super(TreeLayerArtist, self).__init__(*args, **kwargs)

    def clear(self):
        self.treeviewer.redraw()

    def remove(self):
        pass
        #self.treeviewer.redraw()

    def redraw(self):
        self.treeviewer.redraw()

    def update(self):
        # this happens when the subset is changed, but also other places.
        self.treeviewer.redraw()


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
    tools = ["tree:home", "tree:pan", "tree:rectzoom", "tree:lineselect",
             "tree:pointselect"]

    # additional stuff for qt

    # _layer_style_widget_cls = TutorialLayerStateWidget
    # _options_cls =

    def __init__(self, session, state=None, parent=None, widget=None):
        super(TreeDataViewer, self).__init__(session, state=state, parent=parent)

        # TODO move these to treeviewerstate?
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
            self.apply_subset_state,
            self,
            self.state,
            layer=layer,
            layer_state=layer_state,
        )

    def subset_from_selection(self, selectednodes):
        data = self.data

        cid = data.tree_component_id

        # this should be avoided, we are doing the opposite in the glue library code...
        codeidxs = np.isin(data[cid], np.array([n.idx for n in selectednodes]))
        codes = data[cid].codes[codeidxs]

        subset = CategorySubsetState(cid, codes)

        # mode.update(data, subset)

        self.apply_subset_state(subset)

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
            self.data, self.subset_from_selection, self.scene
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

        self.get_title2color()

        if full_equal(self.CACHED_title2color, self.title2color):
            return

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
        self.view.init_values()

        # TODO: can we get rid of init_values here?


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
        self.viewer.view.fitInView(self.viewer.scene.sceneRect(), Qt.KeepAspectRatio)

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
class PointSelect(CheckableTool):

    icon = "glue_point"
    tool_id = "tree:pointselect"
    action_text = "select single nodes at a time"
    tool_tip = "click on a node to select"
    shortcut = "K"

    def __init__(self, viewer):
        super(CheckableTool, self).__init__(viewer)

    def activate(self):
        # the rest of the logic is handled in action controllers in my_actions.py
        self.viewer.view.mouseMode = "pointerselect"

    def deactivate(self):
        self.viewer.view.mouseMode = DEFUALT_MOUSE_MODE

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
        self.viewer.view.setDragMode(self.viewer.view.ScrollHandDrag)

    def deactivate(self):
        self.viewer.view.setDragMode(self.viewer.view.NoDrag)

    def close(self):
        pass



from glue.config import qt_client

qt_client.add(TreeDataViewer)
