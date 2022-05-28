# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 22:38:24 2013

@author: Winand
"""

import sys
import player_bass as bass
from PyQt4 import QtGui

def started():
    links = bass.getOggLinkNumber()
    print "1/"+str(links), bass.getOggTags()
    while(True):
        x = raw_input()
        if x=="":
            QtGui.QApplication.quit()
            break
        elif x.isdigit():
            link = int(x)-1
            if 0 <= link < links:
                bass.goToOggLink(link)
                print x+"/"+str(links), bass.getOggTags()
            else: print "Link not found"
        else: print "Enter link number"

app = QtGui.QApplication(sys.argv)
bass.init()
bass.streamCreate("test.ogg", callback=started)
app.exec_()
bass.destroy()
