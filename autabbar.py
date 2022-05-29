# -*- coding: utf-8 -*-
"""
Created on Thu Oct 03 21:58:47 2013

@author: Winand
"""

from PyQt4.QtCore import Qt, QPoint, QEvent
from PyQt4.QtGui import QTabBar, QPainter, QPen, QColor, QWidget
from general import overmind
from settings import TABBAR

P_LEFT, P_RIGHT = 0, 1
def rcPart(pt, rc):
    return P_RIGHT if pt.x() > rc.left()+rc.width() / 2 else P_LEFT
    
def pointToRect(pt, rc):
    x = min(max(pt.x(), rc.left()), rc.right())
    y = min(max(pt.y(), rc.top()), rc.bottom())
    return QPoint(x, y)

class AuTabBar(QTabBar):
    def __init__(self, parent=None):
        overmind(self).__init__(parent)
        self.movingWidgetVisible = None
        self.setMovable(True)
    
    def __paint_line(self, w, rc):
        p = QPainter(w)
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(TABBAR.ACTIVE_LINE))
        p.setPen(pen)
        p.drawLine(rc.topLeft(), rc.topRight())
    
#    def paintEvent(self, e):
#        overmind(self).paintEvent(e)
#        if not self.movingWidgetVisible:
#            self.__paint_line(self, self.tabRect(self.currentIndex()).adjusted(0,1,1,0))
        
    def tabData(self, index):
        return overmind(self).tabData(index).toPyObject()[0]
        
    def tabsData(self):
        return [self.tabData(i) for i in range(self.count())]
        
    def setTabList(self, items, titleattr):
        for i in range(self.count()): #clear
            self.removeTab(0)
        for i in items:
            self.addTab(getattr(i, titleattr))
            self.setTabData(self.count()-1, (i,))
            
    def mouseMoveEvent(self, e):
        overmind(self).mouseMoveEvent(e)
        if e.buttons() & Qt.LeftButton and self.movingWidgetVisible == None:
            mt = next((x for x in self.findChildren(QWidget) if type(x)==QWidget), None)
            if mt:
                if mt.isVisible():
                    self.movingWidgetVisible = True
                mt.installEventFilter(self)
                
    def eventFilter(self, obj, e):
        if e.type() == QEvent.Paint:
            self.__paint_line(obj, obj.rect().adjusted(2,1,-1,0))
            return True
        elif e.type() == QEvent.Hide:
            self.movingWidgetVisible = False
        elif e.type() == QEvent.Show:
            self.movingWidgetVisible = True
        else:
            print e.type()
        return overmind(self).eventFilter(obj, e)

#class AuTabBar(QTabBar):
#    def __init__(self, parent=None):
#        overmind(self).__init__(parent)
#        self.setMovable(True)
#        self.setAcceptDrops(True)
#        self.m_dragStartPos = None
#        self.dragging = False
#        
#    
#    def mousePressEvent(self, e):
#        if e.button() == Qt.LeftButton:
#            self.m_dragStartPos = e.pos()
#        overmind(self).mousePressEvent(e)
#        
#    def mouseMoveEvent(self, e):
#        if not e.buttons() & Qt.LeftButton or \
#        ((e.pos() - self.m_dragStartPos).manhattanLength()) < \
#        QApplication.startDragDistance():
#            return
#        drag = QDrag(self)
#        mimeData = QMimeData()
#        mimeData.setData("action", "tab-reordering")
#        drag.setMimeData(mimeData)
#        drag.exec_()
#        
#    def dragEnterEvent(self, e):
#        self.dragging = True
#        m = e.mimeData()
#        formats = m.formats()
#        if formats.contains("action") and (m.data("action") == "tab-reordering"):
#            e.acceptProposedAction()
#            
#    def dragMoveEvent(self, e):
#        fromIndex = self.tabAt(self.m_dragStartPos)
#        toIndex = self.tabAt(e.pos())
#        toPart = rcPart(e.pos(), self.tabRect(toIndex))
#        if fromIndex > toIndex and toPart==P_RIGHT: toIndex += 1
#        elif fromIndex < toIndex and toPart==P_LEFT: toIndex -= 1
#        if fromIndex != toIndex:
#            self.moveTab(fromIndex, toIndex)
#            self.m_dragStartPos = pointToRect(e.pos(), self.tabRect(toIndex))
#            print fromIndex, toIndex
#        self.update()
#            
#    def dropEvent(self, e):
#        if not self.dragging: return
#        self.dragging = False
#        e.acceptProposedAction()