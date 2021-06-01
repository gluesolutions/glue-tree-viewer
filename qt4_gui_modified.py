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
import re
import six
import numpy as np

# try:
#     from .qt import QtOpenGL
#     USE_GL = True
# except ImportError:
#     USE_GL = False
USE_GL = False # Temporarily disabled

from qtpy.QtWidgets import *
import qtpy.QtCore as QtCore
from qtpy.QtCore import Qt, QPointF, QLineF
from qtpy.QtGui import *
from ete3.treeview.main import save, _leaf
from ete3.treeview import random_color
from ete3.treeview.qt4_render import render
from ete3.treeview.node_gui_actions import NewickDialog
from ete3 import Tree, TreeStyle

from glue.core.subset import CategorySubsetState

import time

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
        #p.drawRect(self.rect().x(),self.rect().y(),self.rect().width(),self.rect().height())
        p.drawLine(self.line())
        #self.get_nodes_under_line()

    def get_nodes(self):
        return self.selected_cache

    def accumulate_selected(self):
        self.selected_cache += self.get_nodes_under_line()

    def clear_cache(self):
        del self.selected_cache
        self.selected_cache = set()

    def get_nodes_under_line(self):
        #print('-- getting selected nodes')
        #selPath = QPainterPath()
        #selPath.addLine(self.line())
        #elf.scene().setSelectionArea(selPath)

        n2i = self.scene().n2i
        selectednodes = set()
        for node, item in n2i.items():
            #print('node items')

            R = item.mapToScene(item.nodeRegion).boundingRect()

            # change this to four lines if its jank...
            # or one line preferrably
            line1 = QLineF(R.topLeft(), R.bottomRight())
            line2 = QLineF(R.topRight(), R.bottomLeft())

            # WARNING, looks lkie intersect api is different for different types of QT...
            a = line1.intersect(self.line(), QPointF(0, 0))
            b = line2.intersect(self.line(), QPointF(0, 0))
            #print('point1', a)
            #print('point1', b)

            # https://doc.qt.io/qt-5/qlinef-obsolete.html#IntersectType-enum
            self.scene().view.unhighlight_node(node)
            if a == 1 or b == 1:
                #print('collision!!!')
                selectednodes.add(node)
                #self.scene().view.highlight_node(node)
            #else:
                #self.scene().view.unhighlight_node(node)

            #R.adjust(-60, -60, 60, 60)
            

        self.selected_cache = self.selected_cache.union(selectednodes)
        # TODO move drawing to other place
        for node in self.selected_cache:
            self.scene().view.highlight_node(node)

        return selectednodes
    
    def setActive(self,bool):
        self._active = bool

    def isActive(self):
        return self._active

def etime(f):
    def a_wrapper_accepting_arguments(*args, **kargs):
        global TIME
        t1 = time.time()
        f(*args, **kargs)
        print(time.time() - t1)
    return a_wrapper_accepting_arguments


class _TreeView(QGraphicsView):
    def __init__(self, session, func, *args):
        self.session = session
        self.apply_subset_state = func
        QGraphicsView.__init__(self,*args)
        self.buffer_node = None
        self.init_values()

        if USE_GL:
            print("USING GL")
            F = QtOpenGL.QGLFormat()
            F.setSampleBuffers(True)
            print(F.sampleBuffers())
            self.setViewport(QtOpenGL.QGLWidget(F))
            self.setRenderHints(QPainter.Antialiasing)
        else:
            self.setRenderHints(QPainter.Antialiasing or QPainter.SmoothPixmapTransform )

        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHints(QPainter.Antialiasing or QPainter.SmoothPixmapTransform )
        #self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        #self.setOptimizationFlag (QGraphicsView.DontAdjustForAntialiasing)
        self.setOptimizationFlag (QGraphicsView.DontSavePainterState)
        #self.setOptimizationFlag (QGraphicsView.DontClipPainter)
        #self.scene().setItemIndexMethod(QGraphicsScene.NoIndex)
        #self.scene().setBspTreeDepth(24)

    def init_values(self):
        master_item = self.scene().master_item
        self.n2hl = {}
        self.focus_highlight = QGraphicsRectItem(master_item)
        #self.buffer_node = None
        self.focus_node = None
        self.selector = _SelectorItem(master_item)
        self.andSelect = False

    def resizeEvent(self, e):
        QGraphicsView.resizeEvent(self, e)

    def safe_scale(self, xfactor, yfactor):
        self.setTransformationAnchor(self.AnchorUnderMouse)
        xscale = self.transform().m11()
        yscale = self.transform().m22()
        srect = self.sceneRect()

        if (xfactor>1 and xscale>200000) or \
                (yfactor>1 and yscale>200000):
            QMessageBox.information(self, "!",\
                                              "I will take the microscope!")
            return

        # Do not allow to reduce scale to a value producing height or with smaller than 20 pixels
        # No restrictions to zoom in
        if (yfactor<1 and  srect.width() * yscale < 20):
            pass
        elif (xfactor<1 and  srect.width() * xscale < 20):
            pass
        else:
            self.scale(xfactor, yfactor)

    def highlight_node(self, n, fullRegion=False, fg="red", bg="gray", permanent=False):
        self.unhighlight_node(n)
        item = self.scene().n2i[n]
        hl = QGraphicsRectItem(item.content)
        if fullRegion:
            hl.setRect(item.fullRegion)
        else:
            hl.setRect(item.nodeRegion)
        hl.setPen(QColor(fg))
        hl.setBrush(QColor(bg))
        hl.setOpacity(0.2)
        # save info in Scene
        self.n2hl[n] = hl
        if permanent:
            item.highlighted = True

    def unhighlight_node(self, n, reset=False):
        if n in self.n2hl:
            item = self.scene().n2i[n]
            if not item.highlighted:
                self.scene().removeItem(self.n2hl[n])
                del self.n2hl[n]
            elif reset:
                self.scene().removeItem(self.n2hl[n])
                del self.n2hl[n]
                item.highlighted = False
            else:
                pass

    def wheelEvent(self,e):
        # qt4/5
        try:
            delta = e.delta()
        except AttributeError:
            delta = float(e.angleDelta().y())

        factor =  (-delta / 360.0)

        if abs(factor) >= 1:
            factor = 0.0

        # Ctrl+Shift -> Zoom in X
        if  (e.modifiers() & Qt.ControlModifier) and (e.modifiers() & Qt.ShiftModifier):
            self.safe_scale(1+factor, 1)

        # Ctrl+Alt -> Zomm in Y
        elif  (e.modifiers() & Qt.ControlModifier) and (e.modifiers() & Qt.AltModifier):
            self.safe_scale(1,1+factor)

        # Ctrl -> Zoom X,Y
        elif e.modifiers() & Qt.ControlModifier:
            self.safe_scale(1-factor, 1-factor)

        # Shift -> Horizontal scroll
        elif e.modifiers() &  Qt.ShiftModifier:
            if delta > 0:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-20 )
            else:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()+20 )
        # No modifiers ->  Vertival scroll
        else:
            if delta > 0:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()-20 )
            else:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()+20 )

    def set_focus(self, node):
        i = self.scene().n2i[node]
        self.focus_highlight.setPen(QColor("red"))
        self.focus_highlight.setBrush(QColor("SteelBlue"))
        self.focus_highlight.setOpacity(0.2)
        self.focus_highlight.setParentItem(i.content)
        self.focus_highlight.setLine(i.fullRegion)
        self.focus_highlight.setVisible(True)
        self.prop_table.update_properties(node)
        #self.focus_highlight.setLine(i.nodeRegion)
        self.focus_node = node
        self.update()

    def hide_focus(self):
        return
        #self.focus_highlight.setVisible(False)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Shift:
            self.andSelect = False

        QGraphicsView.keyReleaseEvent(self,e)

    def keyPressEvent(self,e):
        key = e.key()
        control = e.modifiers() & Qt.ControlModifier
        shift = e.modifiers() & Qt.ShiftModifier
        if shift:
            print(shift)
            self.andSelect = True
        elif control:
            if key  == Qt.Key_Left:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-20 )
                self.update()
            elif key  == Qt.Key_Right:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()+20 )
                self.update()
            elif key  == Qt.Key_Up:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()-20 )
                self.update()
            elif key  == Qt.Key_Down:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()+20 )
                self.update()
        else:
            if not self.focus_node:
                self.focus_node = self.scene().tree

            if key == Qt.Key_Left:
                if self.focus_node.up:
                    new_focus_node = self.focus_node.up
                    self.set_focus(new_focus_node)
            elif key == Qt.Key_Right:
                if self.focus_node.children:
                    new_focus_node = self.focus_node.children[0]
                    self.set_focus(new_focus_node)
            elif key == Qt.Key_Up:
                if self.focus_node.up:
                    i = self.focus_node.up.children.index(self.focus_node)
                    if i>0:
                        new_focus_node = self.focus_node.up.children[i-1]
                        self.set_focus(new_focus_node)
                    elif self.focus_node.up:
                        self.set_focus(self.focus_node.up)

            elif key == Qt.Key_Down:
                if self.focus_node.up:
                    i = self.focus_node.up.children.index(self.focus_node)
                    if i < len(self.focus_node.up.children)-1:
                        new_focus_node = self.focus_node.up.children[i+1]
                        self.set_focus(new_focus_node)
                    elif self.focus_node.up:
                        self.set_focus(self.focus_node.up)

            elif key == Qt.Key_Escape:
                self.hide_focus()
            elif key == Qt.Key_Enter or\
                    key == Qt.Key_Return:
                print('enter pressed')
                selectednodes = self.selector.get_nodes()

                data = self.session.data_collection[0]

                # this should be avoided, we are doing the opposite in the glue library code...
                codeidxs = np.isin(data['tree nodes'], np.array([n.name for n in selectednodes]))
                codes = data['tree nodes'].codes[codeidxs]
                print('codes', codes)

                subset = CategorySubsetState('tree nodes', codes)

                # mode = self.session.edit_subset_mode
                # mode.update(data, subset)

                self.apply_subset_state(subset)

                #self.prop_table.tableView.setFocus()
            elif key == Qt.Key_Space:
                self.highlight_node(self.focus_node, fullRegion=True,
                                    bg=random_color(l=0.5, s=0.5),
                                    permanent=True)
        QGraphicsView.keyPressEvent(self,e)

    def mouseReleaseEvent(self, e):
        self.scene().view.hide_focus()
        curr_pos = self.mapToScene(e.pos())
        if hasattr(self.selector, "startPoint"):
            x = min(self.selector.startPoint.x(),curr_pos.x())
            y = min(self.selector.startPoint.y(),curr_pos.y())
            w = max(self.selector.startPoint.x(),curr_pos.x()) - x
            h = max(self.selector.startPoint.y(),curr_pos.y()) - y
            if self.selector.startPoint == curr_pos:
                self.selector.setVisible(False)
            self.selector.setActive(False)
        QGraphicsView.mouseReleaseEvent(self,e)

    def mousePressEvent(self,e):
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
        QGraphicsView.mousePressEvent(self,e)

    def mouseMoveEvent(self,e):
        curr_pos = self.mapToScene(e.pos())
        if self.selector.isActive():
            start = self.selector.startPoint
            self.selector.setLine(start.x(), start.y(), curr_pos.x(), curr_pos.y())
            self.selector.get_nodes_under_line()
            #x = min(x(),curr_pos.x())
            #y = min(self.selector.startPoint.y(),curr_pos.y())
            #w = max(self.selector.startPoint.x(),curr_pos.x()) - x
            #h = max(self.selector.startPoint.y(),curr_pos.y()) - y
            #self.selector.setLine(x,y,w,h)
        QGraphicsView.mouseMoveEvent(self, e)


class _BasicNodeActions(object):
    """ Should be added as ActionDelegator """

    @staticmethod
    def init(obj):
        obj.setCursor(Qt.PointingHandCursor)
        obj.setAcceptHoverEvents(True)

    @staticmethod
    def hoverEnterEvent (obj, e):
        print("HOLA")

    @staticmethod
    def hoverLeaveEvent(obj, e):
        print("ADIOS")

    @staticmethod
    def mousePressEvent(obj, e):
        print("Click")

    @staticmethod
    def mouseReleaseEvent(obj, e):
        if e.button() == Qt.RightButton:
            obj.showActionPopup()
        elif e.button() == Qt.LeftButton:
            obj.scene().view.set_focus(obj.node)
            #obj.scene().view.prop_table.update_properties(obj.node)

    @staticmethod
    def hoverEnterEvent (self, e):
        self.scene().view.highlight_node(self.node, fullRegion=True)

    @staticmethod
    def hoverLeaveEvent(self,e):
        self.scene().view.unhighlight_node(self.node)
