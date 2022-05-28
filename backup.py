# -*- coding: utf-8 -*-
"""
Created on Thu Apr 04 00:33:52 2013

@author: Winand
"""

#import player_bass as bass
#__exit=False
#
#def started():
#    links = bass.getOggLinkNumber()
#    while(True):
#        x = raw_input()
#        if x=="":
#            break
#        elif x.isdigit():
#            link = int(x)
#            if link < links:
#                bass.goToOggLink(int(x))
#            else: print "Link not found"
#    bass.destroy()
#    global __exit
#    __exit = True
#    
#bass.init()
#print bass.streamCreate("test.ogg", callback=started)
#
#while(not __exit):
#    pass




#import sys, time
#from PyQt4 import QtCore, QtGui
#
#class WorkThread(QtCore.QThread):
#    def __init__(self):
#        QtCore.QThread.__init__(self)
#
#    def __del__(self):
#        self.wait()
#  
#    def run(self):
#        for i in range(6):
#            time.sleep(0.3) # artificial time delay
#            self.emit( QtCore.SIGNAL('update(QString)'), "from work thread " + str(i) )
#  #app = QtGui.QApplication(sys.argv)
#test = MyApp()
#test.show()
#app.exec_()
#class MyApp(QtGui.QWidget):
#    def __init__(self, parent=None):
#        QtGui.QWidget.__init__(self, parent)
#
#        self.setGeometry(300, 300, 280, 600)
#        self.setWindowTitle('threads')
# 
#        self.layout = QtGui.QVBoxLayout(self)
# 
#        self.testButton = QtGui.QPushButton("test")
#        self.connect(self.testButton, QtCore.SIGNAL("released()"), self.test)
#        self.listwidget = QtGui.QListWidget(self)
# 
#        self.layout.addWidget(self.testButton)
#        self.layout.addWidget(self.listwidget)
#  
#        self.threadPool = []
# 
#    def add(self, text):
#         """ Add item to list widget """
#         print "Add: " + text
#         self.listwidget.addItem(text)
#         self.listwidget.sortItems()
# 
#    def addBatch(self,text="test",iters=6,delay=0.3):
#        """ Add several items to list widget """
#        for i in range(iters):
#            time.sleep(delay) # artificial time delay
#            self.add(text+" "+str(i))
# 
#    def test(self):
#        self.listwidget.clear()
#        # adding entries just from main application: locks ui
#        #  self.addBatch("_non_thread",iters=6,delay=0.3)
#  
#        # adding by emitting signal in different thread
#        self.threadPool.append( WorkThread() )
#        self.connect( self.threadPool[len(self.threadPool)-1], QtCore.SIGNAL("update(QString)"), self.add )
#        self.threadPool[len(self.threadPool)-1].start()
#  
#  
#  # run
#app = QtGui.QApplication(sys.argv)
#test = MyApp()
#test.show()
#app.exec_()