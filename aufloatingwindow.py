# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 16:09:42 2013

@author: Winand
"""

from PyQt4.QtGui import QWidget, QPainter, QCursor, QMouseEvent
from PyQt4.QtCore import Qt, pyqtSignal, QEvent, QCoreApplication
from general import overmind, isInside

class AuFloatingWindow(QWidget):
    paint = pyqtSignal('QPainter')
    
    def __init__(self, parent=None):
        overmind(self).__init__(parent, Qt.FramelessWindowHint|Qt.Tool)
        #self.setAttribute(Qt.WA_ShowWithoutActivating)
        #self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.71)
        self.setMouseTracking(True)
        if parent:
            self.parent = parent
            parent.installEventFilter(self)
        self.tracking = False
        self.inst = QCoreApplication.instance()
        
    def paintEvent(self, e):
        self.paint.emit(QPainter(self))
        
    def mouseMoveEvent(self, e):
        if not self.tracking: return
        gpos = QCursor.pos()
        inside = isInside(gpos, self.parent)
        if inside:
            e = QMouseEvent(QEvent.MouseMove, self.parent.mapFromGlobal(gpos),\
                Qt.NoButton if e.type()!=QEvent.MouseMove else e.button(), \
                Qt.NoButton if e.type()!=QEvent.MouseMove else e.buttons(), \
                Qt.NoModifier) #leaveEvent has no button(), buttons()
            self.inst.notify(self.parent, e)
        else:
            self.inst.notify(self.parent, QEvent(QEvent.Leave))
            
    def mousePressEvent(self,e):
        if self.parent:
            p=self.parent.mapFromGlobal(self.mapToGlobal(e.pos()))
            e = QMouseEvent(QEvent.MouseButtonPress, p,\
                                    e.button(), e.buttons(), Qt.NoModifier)
            self.inst.notify(self.parent, e)
            
    def wheelEvent(self, e):
        if self.parent:
            self.inst.notify(self.parent, e)
        
    def leaveEvent(self, e):
        self.mouseMoveEvent(e) #FIXME may cause problems, has no button(), buttons()
        
    def eventFilter(self, obj, e):
        if e.type() == QEvent.Leave and isInside(QCursor.pos(), obj):
            self.tracking = True
            return True
        elif e.type() == QEvent.Enter and self.tracking:
            self.tracking = False
            return True
        return overmind(self).eventFilter(obj, e)
