from .viewer import HomeButton, ZoomOut, PointSelect, AnimationTool, LineSelect, PanTool# noqa
from .viewer import TreeDataViewer #noqa
#from .my_actions import T_NodeActions

from .utils import read_dendro, read_newick

def setup():
    from glue.config import qt_client
    qt_client.add(TreeDataViewer)
