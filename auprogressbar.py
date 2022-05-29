# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 19:59:26 2013

@author: Winand
"""

from PyQt5.QtCore import pyqtSignal, Qt, QPoint
from PyQt5.QtGui import QPainter, QBrush, QLinearGradient, QColor, QPalette, QPen, QCursor
from PyQt5.QtWidgets import QWidget
from general import overmind, bound

class AuProgressBar(QWidget):
    changed = pyqtSignal(float)
    userChanged = pyqtSignal(float)
    mouseMove = pyqtSignal(int, QPoint)
    BAR_COLOR = "#ffb164"
    
    def __init__(self, parent=None):
        overmind(self).__init__(parent)
        self.setMouseTracking(True)
        self.slim_factor = 4
        self.v = 0
        self.text = {}
    
    def paintEvent(self, e):
        p = QPainter(self)
        rc = self.rect().adjusted(0,self.slim_factor,-1,-1 -self.slim_factor)
        
        if not self.isEnabled():
            rc = self.rect()
            p.setPen(QPen(QColor("#707070"), 0, Qt.DashLine))
            p.drawLine(0, rc.center().y(), rc.width(), rc.center().y())
            return
            
        gr = QLinearGradient(rc.topLeft(), rc.bottomLeft())
        back = self.palette().color(QPalette.Window)
        gr.setColorAt(0, back.darker(112))
        gr.setColorAt(1, back.darker(106))
        p.setBrush(QBrush(gr))
        p.setPen(QColor(back.darker(112)))
        p.drawRoundedRect(rc, 1, 1)
            
        prog_btm = QColor(self.BAR_COLOR)
        p.setPen(QColor(prog_btm.darker(110)))
        v = int(self.v*self.width())
        rc.setRight(v-2)
        if v > 2:
            gr = QLinearGradient(rc.topLeft(), rc.bottomLeft())
            gr.setColorAt(0, prog_btm.lighter(150))
            gr.setColorAt(1, prog_btm)
            p.setBrush(QBrush(gr))
            p.drawRoundedRect(rc, 1, 1)
        elif v > 0: 
            p.drawLine(0,rc.top()+1,0,rc.bottom())
            if v > 1:
                p.drawLine(1,rc.top()+1,1,rc.bottom())
        
        p.setPen(QColor(Qt.black))
        for i in self.text.values():
            offset = i[0][0]
            adjust = 4+offset[0],2+offset[1],-4+offset[0],-2+offset[1]
            rc = self.rect().adjusted(*adjust)
            p.drawText(rc, i[0][1], i[0][2])
            
    def mouseMoveEvent(self, e):
#        gpos = QCursor.pos()
#        gpos.setY(self.mapToGlobal(self.rect().bottomLeft()).y())
#        self.tip.move(gpos)
        if e.buttons() == Qt.LeftButton:
            x, w = float(e.x()), self.width()
            vo, self.v = self.v, max(min(w, x), 0) / w
            if vo != self.v:
                self.userChanged.emit(self.v)
                self.changed.emit(self.v)
                self.repaint()
        self.mouseMove.emit(1, QCursor.pos())
                
    def enterEvent(self, e):
        if not self.isEnabled(): return
        self.mouseMove.emit(0, QCursor.pos())
        
    def leaveEvent(self, e):
        if not self.isEnabled(): return
        self.mouseMove.emit(2, QPoint())
        
    def mousePressEvent(self, e):
        self.mouseMoveEvent(e)
        
    def wheelEvent(self, e):
        vo, self.v = self.v, bound(0, self.v+(.03 if e.angleDelta().y()>0 else -.03), 1)  # https://doc.qt.io/qt-5/qwheelevent-obsolete.html#delta
        print(vo)
        if vo != self.v:
            self.userChanged.emit(self.v)
            self.changed.emit(self.v)
            self.repaint()
        
    @property
    def value(self): return self.v
    @value.setter
    def value(self, v):
        if v != self.v:
            self.v = bound(0, v, 1)
            self.changed.emit(self.v)
            self.repaint()
    
    def valueFromCursor(self):
        r = self.rect().right()
        x = max(min(r, self.mapFromGlobal(QCursor.pos()).x()), 0)
        return x / float(r)
            
    def setTextItem(self, tid, text):
        self.text[tid][0][2] = text
        #self.repaint()
        
    def addTextItem(self, tid, text="", align=Qt.AlignCenter, offset=(0,0)):
        "Add or update text item"
        self.text[tid] = ([offset, align, text],)