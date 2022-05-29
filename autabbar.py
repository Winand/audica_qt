# -*- coding: utf-8 -*-
"""
Created on Thu Oct 03 21:58:47 2013

@author: Winand
"""

# void
# TabBar::mousePressEvent(QMouseEvent* event)
# {
#    if (event->button() == Qt::LeftButton)
#        m_dragStartPos = event->pos(); // m_dragStartPos is a QPoint defined in the header
#    QTabBar::mousePressEvent(event);
# }
#
# void
# TabBar::mouseMoveEvent(QMouseEvent* event)
# {
#    // If the left button isn't pressed anymore then return
#    if (!(event->buttons() & Qt::LeftButton))
#        return;
#
#    // If the distance is too small then return
#    if ((event->pos() - m_dragStartPos).manhattanLength()
#         < QApplication::startDragDistance())
#        return;
#
#    // initiate Drag
#    QDrag* drag = new QDrag(this);
#    QMimeData* mimeData = new QMimeData;
#    // a crude way to distinguish tab-reodering drops from other ones
#    mimeData->setData("action", "tab-reordering") ;
#    drag->setMimeData(mimeData);
#    drag->exec();
# }
#
# void
# TabBar::dragEnterEvent(QDragEnterEvent* event)
# {
#    // Only accept if it's an tab-reordering request
#    const QMimeData* m = event->mimeData();
#    QStringList formats = m->formats();
#    if (formats.contains("action") && (m->data("action") == "tab-reordering")) {
#        event->acceptProposedAction();
#    }
# }
#
# void
# TabBar::dropEvent(QDropEvent* event)
# {
#    int fromIndex   = tabAt(m_dragStartPos);
#    int toIndex     = tabAt(event->pos());
#    
#    // Tell interested objects that 
#    if (fromIndex != toIndex)
#        emit tabMoveRequested(fromIndex, toIndex);
#    event->acceptProposedAction();
# }

from PyQt4.QtCore import pyqtSignal, Qt, QMimeData, QPoint
from PyQt4.QtGui import QTabBar, QDrag, QApplication, QPainter, QPen, QColor
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
    #tabMoveRequested = pyqtSignal(int, int)
    def __init__(self, parent=None):
        overmind(self).__init__(parent)
        self.setAcceptDrops(True)
        self.m_dragStartPos = None
        self.dragging = False
        
    
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_dragStartPos = e.pos()
        overmind(self).mousePressEvent(e)
        
    def mouseMoveEvent(self, e):
        if not self.m_dragStartPos: return
            
        if not e.buttons() & Qt.LeftButton:
            return
            
        if ((e.pos() - self.m_dragStartPos).manhattanLength()) < \
        QApplication.startDragDistance():
            return
            
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setData("action", "tab-reordering")
        drag.setMimeData(mimeData)
        drag.exec_()
        
    def dragEnterEvent(self, e):
        self.dragging = True
        m = e.mimeData()
        formats = m.formats()
        if formats.contains("action") and (m.data("action") == "tab-reordering"):
            e.acceptProposedAction()
            
    def dragMoveEvent(self, e):
        fromIndex = self.tabAt(self.m_dragStartPos)
        toIndex = self.tabAt(e.pos())
        toPart = rcPart(e.pos(), self.tabRect(toIndex))
        if fromIndex > toIndex and toPart==P_RIGHT:
            toIndex += 1
        if fromIndex < toIndex and toPart==P_LEFT:
            toIndex -= 1
        if fromIndex != toIndex:
            self.moveTab(fromIndex, toIndex)
            self.m_dragStartPos = pointToRect(e.pos(), self.tabRect(toIndex))
            print fromIndex, toIndex
        self.mouse_pos = e.pos()
        self.update()
            
    def dropEvent(self, e):
        if not self.dragging: return
        self.dragging = False
#        fromIndex = self.tabAt(self.m_dragStartPos)
#        toIndex = self.tabAt(e.pos())
#        if fromIndex != toIndex:
#            self.moveTab(fromIndex, toIndex)
            #self.tabMoveRequested.emit(fromIndex, toIndex)
        e.acceptProposedAction()
        
    def paintEvent(self, e):
        overmind(self).paintEvent(e)
        p = QPainter(self)
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(TABBAR.ACTIVE_LINE))
        p.setPen(pen)
        rc = self.tabRect(self.currentIndex()).adjusted(0,1,1,0)
        p.drawLine(rc.topLeft(), rc.topRight())
#        if not self.dragging: return
#        fromIndex = self.tabAt(self.m_dragStartPos)
#        toIndex = self.tabAt(self.mouse_pos)
#        if fromIndex == toIndex: return
#        p.setPen(Qt.NoPen)
#        p.setBrush(Qt.Dense6Pattern)
#        p.drawRect(self.tabRect(toIndex).adjusted(2,1,-1,-2))
        
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
        
        
        
                    
#    def dragMoveEvent(self, e):
#        fromIndex = self.tabAt(self.m_dragStartPos)
#        toIndex = self.tabAt(e.pos())
#        if fromIndex != toIndex:
#            self.moveTab(fromIndex, toIndex)
#            self.m_dragStartPos = e.pos()
#            print fromIndex, toIndex
#        self.mouse_pos = e.pos()
#        self.update()
#            
#    def dropEvent(self, e):
#        if not self.dragging: return
#        self.dragging = False
##        fromIndex = self.tabAt(self.m_dragStartPos)
##        toIndex = self.tabAt(e.pos())
##        if fromIndex != toIndex:
##            self.moveTab(fromIndex, toIndex)
#            #self.tabMoveRequested.emit(fromIndex, toIndex)
#        e.acceptProposedAction()
#        
#    def paintEvent(self, e):
#        overmind(self).paintEvent(e)
#        p = QPainter(self)
#        pen = QPen()
#        pen.setWidth(2)
#        pen.setColor(QColor("#ff8000"))
#        p.setPen(pen)
#        rc = self.tabRect(self.currentIndex()).adjusted(0,1,1,0)
#        p.drawLine(rc.topLeft(), rc.topRight())
#        if not self.dragging: return
#        fromIndex = self.tabAt(self.m_dragStartPos)
#        toIndex = self.tabAt(self.mouse_pos)
#        if fromIndex == toIndex: return
#        p.setPen(Qt.NoPen)
#        p.setBrush(Qt.Dense6Pattern)
#        p.drawRect(self.tabRect(toIndex).adjusted(2,1,-1,-2))