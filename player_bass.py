# -*- coding: utf-8 -*-
"""
Created on Wed Apr 03 16:17:49 2013

@author: Winand
"""

from PyQt4 import QtCore
from bass import pybass as bass, pytags as tags
h = 0
    
def __openStream(thread, source):
    global h
    h = bass.BASS_StreamCreateFile(False, source, 0, 0, 0)
#    h = bass.BASS_StreamCreateURL(u'http://94.25.53.133/ultra-192.m3u', 0, \
#        bass.BASS_STREAM_BLOCK + bass.BASS_STREAM_STATUS + bass.BASS_STREAM_AUTOFREE + bass.BASS_UNICODE, bass.DOWNLOADPROC(), 0)
#    print bass.BASS_ErrorGetCode()
#    print h
    bass.BASS_ChannelPlay(h, False)
    thread.emit(QtCore.SIGNAL('stream_loaded()'))
        
def streamCreate(source, is_remote=0, offset=0, length=0, callback=None):
    thd = GenericThread(__openStream, source)
    QtCore.QObject.connect(thd, QtCore.SIGNAL("stream_loaded()"), callback)
    thd.start()
    
def init():
    return bass.BASS_Init(-1, 44100, 0, 0, 0)
    
def destroy():
    bass.BASS_StreamFree(h)
    bass.BASS_Free()
    #bass.BASS_PluginFree(0)
    
def getOggLinkNumber():
    return bass.BASS_ChannelGetLength(h, bass.BASS_POS_OGG)
    
def goToOggLink(link):
    #print bass.BASS_ChannelGetPosition(h, bass.BASS_POS_OGG)
    bass.BASS_ChannelSetPosition(h, link, bass.BASS_POS_OGG)
    
def getOggTags():
    print tags.TAGS_Read(h, "%UTF8(%ALBM\6%ARTI\6%CMNT\6%COMP\6%COPY\6%GNRE\6%TITL\6%TRCK\6%YEAR)")==tags.TAGS_Read(h, "%UTF8(%IFV1(%ALBM,%ALBM)\6%IFV1(%ARTI,%ARTI)\6%IFV1(%CMNT,%CMNT)\6%IFV1(%COMP,%COMP)\6%IFV1(%COPY,%COPY)\6%IFV1(%GNRE,%GNRE)\6%IFV1(%TITL,%TITL)\6%IFV1(%TRCK,%TRCK)\6%YEAR)")
    return tags.TAGS_Read(h, "%UTF8(%ALBM\6%ARTI\6%CMNT\6%COMP\6%COPY\6%GNRE\6%TITL\6%TRCK\6%YEAR\6%SUBT\6%AART\6%DISC)").split('\6')
    
class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs
 
    def __del__(self):
        self.wait()
 
    def run(self):
        self.function(self, *self.args,**self.kwargs)
