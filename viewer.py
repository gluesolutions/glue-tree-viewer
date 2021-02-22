# TODO make it possible to load tree data using a factory
# TODO make it possible to view using ete

# this file based on http://docs.glueviz.org/en/stable/customizing_guide/viewer.html


# -- VIEWER STATE CLASS
from glue.viewers.common.state import ViewerState
from glue.external.echo import CallbackProperty

class TreeViewerState(ViewerState):
    scale_att = CallbackProperty(docstring='The scale of the tree')
    fill = CallbackProperty(docstring='Draw the glyphs of nodes in tree')

    def scale_att_callback(value):
        print('new scale value is ', value)

    def fill_att_callback(value):
        print('new draw heads value is ', value)

    def __init__(self, *args, **kwargs):
        # QUESTION: sometimes `, self` is required in super call, sometimes not
        super(TreeViewerState).__init__(*args, **kwargs)
        self.add_callback('scale_att', self.scale_att_callback)
        self.add_callback('fill', self.fill_att_callback)

# -- LAYER STATE
from glue.viewers.common.state import LayerState

class TreeLayerState(LayerState):
    # not sure what layers mean in tree context yet
    # maybe this will include just drawing parameters like node size, node glyph settings, branch label, etc
    pass

# -- LAYER ARTIST
from glue.viewers.common.layer_artist import LayerArtist

class TreeLayerArtist(LayerArtist):
    __layer_artist_cls = TreeLayerState

    def __init__(self, *args, **kwargs):
        super(TreeLayerArtist, self).__init__(*args, **kwargs)

    def clear(self):
        pass
    def remove(self):
        pass
    def redraw(self):
        pass
    def update(self):
        pass

# -- QT special widgets
# --- LayerStateWidget

from glue.external.echo.qt import connect_checkable_button
from qtpy.QtWidgets import QWidget, QVBoxLayout, QCheckBox

class TreeLayerStateWidget(QWidget):
    def __init__(self, layer_artist):
        # QUESTION: why is LayerEditWidget different from QWidget ??
        super(LayerEditWidget, self).__init__()

        # TODO: reconcile this with above class which had scale option
        self.checkbox = QCheckBox('draw node heads')

        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        self.setLayout(layout)

        self.layer_state = layer_artist.state
        connect_checkable_button(self.layer_state, 'fill', self.checkbox)

# --- ViewerStateWidget
class TreeViewerStateWidget(QWidget):
    def __init__(self, viewer_state, session=None):
        super(TreeViewerStateWidget, self).__init__()

        # viewer state has no callbacks/properties yet, only layer state
        # so we just have empty layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.viewer_state = viewer_state

# -- FINAL: DATA VIEWER CLASS
from glue.viewers.common.qt.data_viewer import DataViewer
from matplotlib import pyplot as plt

class TreeDataViewer(DataViewer):
    LABEL = 'ete3 based Tree Viewer'
    _state_cls = TreeViewerState
    _data_artist_cls = TreeLayerArtist
    _subset_artist_cls = TreeLayerArtist

    # additional stuff for qt
    _options_cls = TreeViewerStateWidget
    _layer_style_widget_cls = TreeLayerStateWidget

    def __init__(self, *args, **kwargs):
        super(TreeDataViewer, self).__init__(*args, **kwargs)
        self.axes = plt.subplot(1, 1, 1)
        self.setCentralWidget(self.axes.figure.canvas)

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        # QUESTION: is cls gonna TreeLayerArtist? and do i need to update its constructor to include axes and state argument?
        # QUESTION: also, where does self.state come from? guess: from superclass, Viewer, and is an instantiation of TreeViewerState
        return cls(self.axes, self.state, layer=layer, layer_state=layer_state)



from glue.config import qt_client
qt_client.add(TreeDataViewer)
