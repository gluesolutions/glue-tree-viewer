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

    def init_treedrawing(self, data):
        #TODO move I think this should be in dataviewer class
        self.data = data
        t = self.data.tdata


        # do qt stuff {

        # show_tree stuff {

        scene, ts = _TreeScene(), ete3.TreeStyle()

        
        # set style of nodes appropirate to sublcasses

        self.scene = scene

        tree_item, n2i, n2f = render(t, ts)
        scene.init_values(t, ts, n2i, n2f)

        tree_item.setParentItem(scene.master_item)
        scene.addItem(scene.master_item)

        # }

        # _GUI class stuff {

        self.scene.GUI = self
        self.view = _TreeView(self.session, self.apply_subset_state, self.scene)
        self.scene.view = self.view
        self.node_properties = None
        self.view.prop_table = None

        # }


        self.setCentralWidget(self.view)

        self.redraw()

        return True

    def __init__(self, fn, session, apply_subset_state, parent, *args, **kwargs):
        self.treeviewer = parent
        super(TreeLayerArtist, self).__init__(*args, **kwargs)
        print('tree layer artist being initialzied')
        self.setCentralWidget = fn
        self.session = session
        self.apply_subset_state = apply_subset_state

        self.state.add_callback('fill', self._on_fill_checked)
        self.init_treedrawing(self.state.layer.data)

    def clear(self):
        print("clear1")

    def remove(self):
        print("remove1")

    def redraw(self):
        self.scene.draw()
        self.view.init_values()

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
from glue.core.subset import Subset


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
        self.s = session

        assert isinstance(self.state, ViewerState)
        self.state.add_callback('layers', self._on_layers_changed)
        from collections import defaultdict
        self.title2color = defaultdict((lambda: "#000000"))

    def add_data(self, data):
        print('adding data')
        return super(TreeDataViewer, self).add_data(data)

    #def add_subset(self, subset):
        #print('adding subset')
        ##if subset.data != self.data:
            ##raise ValueError("subset parent data does not match existing tree data")
        #return super(TreeDataViewer, self).add_subset(subset)

    def _on_layers_changed(self, *args):
        for layerstate in self.layers:
            print('layerstate', layerstate)
            if layerstate.visible:
                layer = layerstate.layer
                if isinstance(layer, Subset):
                    import pdb
                    pdb.set_trace()
                    print('subset_mask')
                    print(layer.to_mask())
                    print('longlen', len(layer.data['tree nodes']))
                    print('shortlen', len(layer.data['tree nodes'][layer.to_mask()]))
                    goodnames = layer.data['tree nodes'][layer.to_mask()]
                    for name in goodnames:
                        self.title2color[name] = layer.style.color
                    #{ make code to tree node conversion }
                    print('found subset')

                    for node in layer.data.tdata.traverse():
                        print('node.title', node.name)
                        st = ete3.NodeStyle()
                        color = self.title2color[node.name]
                        if color != "#000000":
                            print('found !!!', color)
                            st["bgcolor"] = color
                            node.set_style(st)
                else:
                    assert hasattr(layer, 'tdata')
                

        print('layers chagned')

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        # QUESTION: also, where does self.state come from? guess: from superclass, Viewer, and is an instantiation of TreeViewerState
        assert cls == TreeLayerArtist
        return cls(self.setCentralWidget, self.s, 
                   self.apply_subset_state, self, self.state, layer=layer, layer_state=layer_state)
    

    


from glue.config import qt_client

qt_client.add(TreeDataViewer)

# BUG: we can't save the session

# how to send links from tree viewer

# PERFORMANCE:  only do collision checks when the selection line changes, not every frame.

# TODO
# press enter to submit subset
   # https://github.com/glue-viz/glue/blob/241edb32ab6f4a82adf02ef3711c16342fd214ed/glue/viewers/table/qt/data_viewer.py#L251
# display subsets on tree

# TODO use https://github.com/glue-viz/glue/blob/241edb32ab6f4a82adf02ef3711c16342fd214ed/glue/utils/array.py#L497 this class to represent trees?
