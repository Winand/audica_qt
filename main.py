# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 22:38:24 2013

@author: Winand
"""

import sys
import player_bass as bass
from PyQt5 import QtWidgets, QtCore

def started():
    links = bass.getOggLinkNumber()
    print("1/"+str(links), bass.getOggTags())
    while(True):
        x = input()
        if x=="":
            QtWidgets.QApplication.quit()
            break
        elif x.isdigit():
            link = int(x)-1
            if 0 <= link < links:
                bass.goToOggLink(link)
                print(x+"/"+str(links), bass.getOggTags())
            else: print("Link not found")
        else: print("Enter link number")

app = QtWidgets.QApplication(sys.argv)
QtCore.pyqtRemoveInputHook()  # "The event loop is already running" https://stackoverflow.com/a/40181398
bass.init()
bass.streamCreate("test.ogg", callback=started)
app.exec_()
bass.destroy()
