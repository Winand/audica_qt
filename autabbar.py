# -*- coding: utf-8 -*-
"""
Created on Thu Oct 03 21:58:47 2013

@author: Winand
"""

from PyQt5.QtCore import Qt, QPoint, QEvent, QEasingCurve, QVariantAnimation, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QTabBar, QWidget, QLineEdit
from general import overmind
from settings import TABBAR as P

P_LEFT, P_RIGHT = 0, 1
def rcPart(pt, rc):
    return P_RIGHT if pt.x() > rc.left()+rc.width() / 2 else P_LEFT
    
def pointToRect(pt, rc):
    x = min(max(pt.x(), rc.left()), rc.right())
    y = min(max(pt.y(), rc.top()), rc.bottom())
    return QPoint(x, y)
    
class AuAnimStub(QVariantAnimation):
    def updateCurrentValue(self, value): pass
    def updateState(self, newState, oldState): self.parent().update()

class AuTabBar(QTabBar):
    changed = pyqtSignal() #called on insert/remove/reorder tabs
    
    def __init__(self, parent=None):
        overmind(self).__init__(parent)
        self.setMovable(True)
        self.movingWidgetVisible = None
        self.anim = AuAnimStub(self)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.editor = QLineEdit(self)
        self.editor.hide()
        self.editor.setAlignment(Qt.AlignHCenter)
        self.editor.installEventFilter(self)
        self.tabMoved.connect(lambda from_,to:self.changed.emit())
        self.currentChanged.connect(lambda index:self.changed.emit())
    
    def __paint_line(self, w, rc):
        p = QPainter(w)
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(P.ACTIVE_LINE))
        p.setPen(pen)
        p.drawLine(rc.topLeft(), rc.topRight())
    
    def paintEvent(self, e):
        overmind(self).paintEvent(e)
        if not self.movingWidgetVisible and self.anim.state() == 0:
            self.__paint_line(self, self.tabRect(self.currentIndex()).adjusted(0,1,1,0))
        elif self.anim.state() == 2:
            v,_ = self.anim.currentValue().toInt()
            self.__paint_line(self, self.mt_rc().adjusted(2+v,1,-1+v,0))
        if not self.editor.isHidden():
            self.editor.setGeometry( \
                        self.tabRect(self.currentIndex()).adjusted(1,2,-1,-2))
        
    def tabData(self, index):
        return overmind(self).tabData(index)[0]
        
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
                self.mt_rc = mt.rect
                
    def mousePressEvent(self, e):
        self.editor.hide()
        overmind(self).mousePressEvent(e)
        
    def tabInserted(self, index): self.changed.emit()
    def tabRemoved(self, index): self.changed.emit()
                
    def eventFilter(self, obj, e):
        if obj == self.editor:
            if e.type() == QEvent.KeyPress:
                if e.key() in (Qt.Key_Enter, Qt.Key_Return):
                    self.setTabText(self.currentIndex(), self.editor.text())
                    self.editor.hide()
                elif e.key() == Qt.Key_Escape:
                    self.editor.hide()
            elif e.type() == QEvent.FocusOut:
                self.editor.hide()
        else:
            if e.type() == QEvent.Paint:
                self.__paint_line(obj, obj.rect().adjusted(2,1,-1,0))
                return True
            if e.type() == QEvent.Hide:
    #        int length = d->tabList[d->pressedIndex].dragOffset;
    #        int width = verticalTabs(d->shape)
    #            ? tabRect(d->pressedIndex).height()
    #            : tabRect(d->pressedIndex).width();
    #        int duration = qMin(ANIMATION_DURATION,
    #                (qAbs(length) * ANIMATION_DURATION) / width);
                rc = self.tabRect(self.currentIndex())
                slide_offset = float(abs(obj.x() - rc.x()))
                time_offset = min(slide_offset/rc.width(), 1)*250
                self.anim.setStartValue(obj.x())
                self.anim.setEndValue(rc.x())
                self.anim.setDuration(time_offset)
                self.anim.start()
                self.movingWidgetVisible = False
            elif e.type() == QEvent.Show:
                self.movingWidgetVisible = True
        return overmind(self).eventFilter(obj, e)
        
    def mouseDoubleClickEvent(self, e):
        self.__start_tab_rename()
        
    def __start_tab_rename(self):
        self.editor.setText(self.tabText(self.currentIndex()))
        self.editor.selectAll()
        self.editor.setGeometry(self.tabRect(self.currentIndex()).adjusted(1,2,-1,-2))
        self.editor.show()
        self.editor.setFocus()

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