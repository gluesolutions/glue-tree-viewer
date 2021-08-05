# COPIED FROM https://github.com/etetoolkit/ete/blob/master/ete3/treeview/qt4_gui.py BY THOMAS MORRISS ON APRIL 5, 2021 !!!!!!!!
# #START_LICENSE###########################################################
#
#
# This file is part of the Environment for Tree Exploration program
# (ETE).  http://etetoolkit.org
#
# ETE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ETE is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ETE.  If not, see <http://www.gnu.org/licenses/>.
#
#
#                     ABOUT THE ETE PACKAGE
#                     =====================
#
# ETE is distributed under the GPL copyleft license (2008-2015).
#
# If you make use of ETE in published work, please cite:
#
# Jaime Huerta-Cepas, Joaquin Dopazo and Toni Gabaldon.
# ETE: a python Environment for Tree Exploration. Jaime BMC
# Bioinformatics 2010,:24doi:10.1186/1471-2105-11-24
#
# Note that extra references to the specific methods implemented in
# the toolkit may be available in the documentation.
#
# More info at http://etetoolkit.org. Contact: huerta@embl.de
#
#
# #END_LICENSE#############################################################
from __future__ import absolute_import
from __future__ import print_function
import six

# try:
#     from .qt import QtOpenGL
#     USE_GL = True
# except ImportError:
#     USE_GL = False

USE_GL = False

from qtpy.QtWidgets import *
import qtpy.QtCore as QtCore
from qtpy.QtCore import Qt, QPointF, QLineF
from qtpy.QtGui import *

import my_actions as ma


from ete3.treeview.qt4_render import render

from ete3 import Tree, TreeStyle
from ete3.treeview import random_color



def etime(f):
    import time
    def a_wrapper_accepting_arguments(*args, **kargs):
        global TIME
        t1 = time.time()
        f(*args, **kargs)
        print(time.time() - t1)

    return a_wrapper_accepting_arguments


class scrollenabled():
    def __init__(self, on):
        self.on = on

    def __enter__(self):
        self.on.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.on.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def __exit__(self, type, value, traceback):
        self.on.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.on.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

class _ZoomboxItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        QGraphicsRectItem.__init__(self, 0, 0, 0, 0)
        self.Color = QColor("blue")

        self._active = False

        if parent:
            self.setParentItem(parent)

    def paint(self, p, option, widget):
        p.setPen(self.Color)
        p.setBrush(QBrush(Qt.NoBrush))
        p.drawRect(
            self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height()
        )


def get_hlbox(node, item):
    if hasattr(item, 'highlightbox'):
        return item.highlightbox
    else:
        hlbox = item.nodeRegion

        if not node.is_leaf():
            centery = item.center
            hlbox.setTop(centery - 5)
            hlbox.setBottom(centery + 5)

        item.highlightbox = hlbox
        return hlbox

class _SelectorItem(QGraphicsLineItem):
    def __init__(self, parent=None):
        self.Color = QColor("blue")
        self._active = False
        QGraphicsLineItem.__init__(self, 0, 0, 0, 0)
        self.selected_cache = set()

        if parent:
            self.setParentItem(parent)

    def paint(self, p, option, widget):
        p.setPen(self.Color)
        p.setBrush(QBrush(Qt.NoBrush))
        p.drawLine(self.line())

    def get_nodes(self):
        return self.selected_cache

    def accumulate_selected(self):
        self.selected_cache |= self.get_nodes_under_line()

    def clear_cache(self):
        self.scene().view.unhighlight_all()

        del self.selected_cache
        self.selected_cache = set()

        

    def get_nodes_under_line(self):
        n2i = self.scene().n2i
        selectednodes = set()
        for node, item in n2i.items():

            hlbox = get_hlbox(node, item)

            R = item.mapToScene(hlbox).boundingRect()

            line1 = QLineF(R.topLeft(), R.bottomRight())
            line2 = QLineF(R.topRight(), R.bottomLeft())

            # WARNING, looks lkie intersect api is different for different types of QT...
            a = line1.intersect(self.line(), QPointF(0, 0))
            b = line2.intersect(self.line(), QPointF(0, 0))

            # https://doc.qt.io/qt-5/qlinef-obsolete.html#IntersectType-enum
            self.scene().view.unhighlight_node(node)
            if a == 1 or b == 1:
                selectednodes.add(node)

        for node in self.selected_cache:
            self.scene().view.highlight_node(node)

        for node in selectednodes:
            self.scene().view.highlight_node(node)

        return selectednodes

    def setActive(self, bool):
        self._active = bool

    def isActive(self):
        return self._active


class _TreeView(QGraphicsView):

    def __init__(self, data, func, scene):
        QGraphicsView.__init__(self, scene)

        # tree data
        self.data = data
        # callback function for selected nodes
        self.subset_from_selection = func

        self.init_values()

        if USE_GL:
            print("USING GL")
            F = QtOpenGL.QGLFormat()
            F.setSampleBuffers(True)
            print(F.sampleBuffers())
            self.setViewport(QtOpenGL.QGLWidget(F))
            self.setRenderHints(QPainter.Antialiasing)
        else:
            self.setRenderHints(QPainter.Antialiasing or QPainter.SmoothPixmapTransform)

        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHints(QPainter.Antialiasing or QPainter.SmoothPixmapTransform)
        # self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        # self.setOptimizationFlag (QGraphicsView.DontAdjustForAntialiasing)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState)
        # self.setOptimizationFlag (QGraphicsView.DontClipPainter)
        # self.scene().setItemIndexMethod(QGraphicsScene.NoIndex)
        # self.scene().setBspTreeDepth(24)

        self.mouseMode = "none"


    def init_values(self):
        master_item = self.scene().master_item
        self.n2hl = {}
        self.selector = _SelectorItem(parent=master_item)
        self.zoomrect = _ZoomboxItem(parent=master_item)

        self.andSelect = False

        self.actionControllers  = set()

    def resizeEvent(self, e):
        QGraphicsView.resizeEvent(self, e)

    def safe_scale(self, xfactor, yfactor):
        self.setTransformationAnchor(self.AnchorUnderMouse)
        xscale = self.transform().m11()
        yscale = self.transform().m22()
        srect = self.sceneRect()

        if (xfactor > 1 and xscale > 200000) or (yfactor > 1 and yscale > 200000):
            QMessageBox.information(self, "!", "I will take the microscope!")
            return

        # Do not allow to reduce scale to a value producing height or with smaller than 20 pixels
        # No restrictions to zoom in
        if yfactor < 1 and srect.width() * yscale < 20:
            pass
        elif xfactor < 1 and srect.width() * xscale < 20:
            pass
        else:
            self.scale(xfactor, yfactor)

    def highlight_node(self, n, fullRegion=False, fg="red", bg="gray", permanent=False):

        if n in self.n2hl:
            # don't rehightlight an already higlighted node
            return None

        item = self.scene().n2i[n]
        hl = QGraphicsRectItem(item.content)

        hl.setRect(get_hlbox(n, item))

        hl.setPen(QColor(fg))
        hl.setBrush(QColor(bg))
        hl.setOpacity(0.2)

        # save info in Scene
        self.n2hl[n] = hl

    def unhighlight_node(self, n, reset=False):
        if n in self.n2hl:
            item = self.scene().n2i[n]
            self.scene().removeItem(self.n2hl[n])
            del self.n2hl[n]

    def unhighlight_all(self):
        for n in self.n2hl:
            item = self.scene().n2i[n]
            self.scene().removeItem(self.n2hl[n])

        del self.n2hl
        self.n2hl = {}

    def wheelEvent(self, e):
        # qt4/5
        try:
            delta = e.delta()
        except AttributeError:
            delta = float(e.angleDelta().y())

        factor = -delta / 360.0

        if abs(factor) >= 1:
            factor = 0.0

        # Ctrl+Shift -> Zoom in X
        if (e.modifiers() & Qt.ControlModifier) and (e.modifiers() & Qt.ShiftModifier):
            self.safe_scale(1 + factor, 1)

        # Ctrl+Alt -> Zomm in Y
        elif (e.modifiers() & Qt.ControlModifier) and (e.modifiers() & Qt.AltModifier):
            self.safe_scale(1, 1 + factor)

        # Ctrl -> Zoom X,Y
        elif e.modifiers() & Qt.ControlModifier:
            self.safe_scale(1 - factor, 1 - factor)

        # Shift -> Horizontal scroll
        elif e.modifiers() & Qt.ShiftModifier:
            if delta > 0:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - 20
                )
            else:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() + 20
                )
        # No modifiers ->  Vertival scroll
        else:
            if delta > 0:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - 20)
            else:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() + 20)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Shift:
            self.andSelect = False

        QGraphicsView.keyReleaseEvent(self, e)


    def keyPressEvent(self, e):
        key = e.key()
        control = e.modifiers() & Qt.ControlModifier
        shift = e.modifiers() & Qt.ShiftModifier
        if shift:
            self.andSelect = True
        else:

            # check not active so that you cant press enter before releasing mouse
            if (
                key == Qt.Key_Enter
                or key == Qt.Key_Return
                and not self.selector.isActive()
            ):
                #{A} refactor this into method in other file (probably state)
                selectednodes = self.selector.get_nodes()

                # make sure visual state is synced with what goes into glue
                a = set([node for node, _ in self.n2hl.items()])
                assert a == selectednodes

                self.subset_from_selection(selectednodes)


        #QGraphicsView.keyPressEvent(self, e)

    def mouseReleaseEvent(self, e):

        if self.mouseMode == "lineselect":
            self.selector.accumulate_selected()
            self.selector.setActive(False)
            self.selector.setVisible(False)
        if self.mouseMode == "rectzoom":
            # convert rect to have positive coordinates
            rect = self.zoomrect.rect()
            normd = rect.normalized()
            # {A}

            with scrollenabled(self):
                self.fitInView(normd, Qt.KeepAspectRatioByExpanding)

            # self.ensureVisible(normd, 10, 10)
            # self.centerOn(normd.center())

            self.zoomrect.setActive(False)
            self.zoomrect.setVisible(False)

            
        QGraphicsView.mouseReleaseEvent(self, e)

    def mousePressEvent(self, e):
        if self.mouseMode == "lineselect":
            pos = self.mapToScene(e.pos())
            x, y = pos.x(), pos.y()
            if self.andSelect:
                self.selector.accumulate_selected()
            else:
                self.selector.clear_cache()

            self.selector.setLine(x, y, x, y)
            self.selector.startPoint = QPointF(x, y)

            self.selector.setActive(True)
            self.selector.setVisible(True)

        elif self.mouseMode == "rectzoom":
            pos = self.mapToScene(e.pos())
            x, y = pos.x(), pos.y()

            self.zoomrect.setRect(x, y, 0, 0)
            self.zoomrect.setActive(True)
            self.zoomrect.setVisible(True)

        # NOTE: if we want to add mouse click selection, we have to overwrite the mousePressEvent methods in
        #            node_gui_actions
        QGraphicsView.mousePressEvent(self, e)

    def mouseMoveEvent(self, e):
        if self.mouseMode == "lineselect":

            if self.selector.isActive():
                curr_pos = self.mapToScene(e.pos())
                start = self.selector.startPoint
                self.selector.setLine(start.x(), start.y(), curr_pos.x(), curr_pos.y())
                self.selector.get_nodes_under_line()

        elif self.mouseMode == "rectzoom":

            if self.zoomrect.isActive():
                curr_pos = self.mapToScene(e.pos())
                r = self.zoomrect.rect()
                w = curr_pos.x() - r.x()
                h = curr_pos.y() - r.y()
                self.zoomrect.setRect(r.x(), r.y(), w, h)

        QGraphicsView.mouseMoveEvent(self, e)
