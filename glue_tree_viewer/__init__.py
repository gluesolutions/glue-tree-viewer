from .viewer import HomeButton, ZoomOut, PointSelect, AnimationTool, LineSelect, PanTool# noqa
from .viewer import TreeDataViewer #noqa
from .utils import Link_Index_By_Value
#from .my_actions import T_NodeActions

def setup():
    from glue.config import qt_client
    qt_client.add(TreeDataViewer)
