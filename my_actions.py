# class to be monkey patched into ete3

# from __future__ import absolute_import
# from functools import partial
# from six.moves import range
#
# from .qt import Qt, QDialog, QMenu, QCursor, QInputDialog
# from .svg_colors import random_color
# from . import  _show_newick
# from ..evol import EvolTree

from qtpy.QtCore import Qt


class T_NodeActions(object):
    """ Used to extend QGraphicsItem features """

    def __init__(self):
        self.setAcceptHoverEvents(True)
        self.disable()

    def enable(self):
        self._enabled = True
        self.setCursor(Qt.PointingHandCursor)

    def disable(self):
        self._enabled = False
        self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, e):

        if not self.node:
            return

        if (
            self.scene().view.mouseMode == "pointerselect"
            and e.button() == Qt.LeftButton
        ):
            self.scene().view.subset_from_selection([self.node])

    def hoverEnterEvent(self, e):
        if self.scene().view.mouseMode == "pointerselect":
            self.enable()
        else:
            self.disable()

        if self.node and self._enabled:
            self.scene().view.highlight_node(self.node)


    def hoverLeaveEvent(self, e):
        if self.node and self._enabled:
            if self.node in self.scene().view.n2hl:
                self.scene().view.unhighlight_node(self.node, reset=False)

    def mousePressEvent(self, e):
        if self._enabled:
            pass
