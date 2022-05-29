# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 18:23:15 2013

@author: Winand
"""

import sys
if sys.platform == 'win32':
    from windows.com import GetKeyboardLayoutName
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt, QEvent
from general import overmind
    
class AuLineEdit(QLineEdit):
    
    def __init__(self, *args, **kwargs):
        overmind(self).__init__(*args, **kwargs)
        self.layout = self.getLayoutName()
        self.showLayout = False
        
    def paintEvent(self, e):
        overmind(self).paintEvent(e)
        if not self.showLayout:
            return
        rc = self.rect().adjusted(0, 0, -4, 0)
        p = QPainter(self)
        p.setPen(Qt.gray)
        p.drawText(rc, Qt.AlignVCenter|Qt.AlignRight, self.layout)
        
    def changeEvent(self, e):
        if e.type() == QEvent.KeyboardLayoutChange:
            self.layout = self.getLayoutName()
            self.update()
            
    def focusInEvent(self, e):
        self.showLayout = True
        overmind(self).focusInEvent(e)
        
    def focusOutEvent(self, e):
        self.showLayout = False
        overmind(self).focusOutEvent(e)
        
    def getLayoutName(self):
        return GetKeyboardLayoutName() if sys.platform == 'win32' \
                else '' #FIXME: needs solutions for other platforms