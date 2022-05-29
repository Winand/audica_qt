# -*- coding: utf-8 -*-
"""
Created on Wed Apr 03 16:17:49 2013

@author: Winand
"""

import sys
from PyQt5 import QtCore
from threading import Lock
from bass import pybass as bass, pytags as tags
import glob
from playlist import PlayItem
from general import CTypesReader, wr, overmind
from struct import unpack
from glob import iglob
from os.path import dirname, isfile, join, splitext
from PyQt5.QtGui import QPixmap
from ctypes import c_float, byref
from settings import PLAYER_BASS as P
MULTITHREADED = False
MIDI_SOUNDFONT = u"Scc1t2.sf2"
BASS_CTYPE_STREAM_MIDI = 0x10d00 #bassmidi
lock_tags = Lock()

Plugin_list = {} #plugin names
builtInStreamFs = ("mp3", "mp2", "mp1", "ogg", "wav", "aif")
builtInMusicFs = ("mo3", "it", "xm", "s3m", "mtm", "mod", "umx")
builtInFormats = "*." + " *.".join(builtInStreamFs) + " *." + " *.".join(builtInMusicFs) #all built-in supported formats
Filter = ["BASS built-in (" + builtInFormats + ")"]
    
class Player(QtCore.QObject):
    stream_loaded = QtCore.pyqtSignal("PyQt_PyObject", bool)

    def __init__(self):
        overmind(self).__init__()
        self.__resetPlayItem() #PlayItem dummy
        self.unsync = False
    
    #TODO try to load stream/music according to file ext at first, another method on fail
    def __openStream(self, thread, source, is_remote):
        #self.p = PlayItem()
        self.p.path = source
        self.p.remote = is_remote
        self.p.stream = True #try to interpret as a stream at first
        if is_remote:
            self.p.handle = bass.BASS_StreamCreateURL(source, 0, \
                bass.BASS_STREAM_BLOCK|bass.BASS_STREAM_AUTOFREE|bass.BASS_UNICODE, bass.DOWNLOADPROC(), 0) #bass.BASS_STREAM_STATUS
        else:
            self.p.handle = bass.BASS_StreamCreateFile(False, source, 0, 0, bass.BASS_UNICODE)
            if not self.p.handle and bass.BASS_ErrorGetCode() == bass.BASS_ERROR_FILEFORM: #wrong file format try HMUSIC
                self.p.stream = False
                self.p.handle = bass.BASS_MusicLoad(False, source, 0, 0, bass.BASS_MUSIC_PRESCAN|bass.BASS_UNICODE, 0)

        if not self.p.handle: #open failed, reset
            self.__resetPlayItem()
        else:
            l=bass.BASS_ChannelGetLength(self.p.handle, bass.BASS_POS_BYTE)
            tl=bass.BASS_ChannelBytes2Seconds(self.p.handle, l)
            self.p.timing = tl
        self.stream_loaded.emit(self, self.p.handle != 0)
            
    def streamCreate(self, pi, offset=0, length=0, callback=None):
        if MULTITHREADED:
            thd = GenericThread(self.__openStream, pi.path, pi.remote)
            QtCore.QObject.connect(thd, QtCore.SIGNAL("stream_loaded(PyQt_PyObject, bool)"), callback)
            thd.start()
        else:
            self.stream_loaded.connect(callback)
            self.__openStream(self, pi.path, pi.remote)
        
    def streamPlay(self):
        return bass.BASS_ChannelPlay(self.p.handle, False)
    
    def getOggLinkNumber(self):
        return bass.BASS_ChannelGetLength(self.p.handle, bass.BASS_POS_OGG)
        
    def goToOggLink(self, link):
        bass.BASS_ChannelSetPosition(self.p.handle, link, bass.BASS_POS_OGG)
        print(bass.BASS_StreamGetFilePosition(self.p.handle, bass.BASS_FILEPOS_CURRENT))
            
    def getpos(self):
        print("Current byte position is", bass.BASS_ChannelGetPosition(self.p.handle, bass.BASS_POS_BYTE), \
            bass.BASS_StreamGetFilePosition(self.p.handle, bass.BASS_FILEPOS_CURRENT), \
            bass.BASS_ChannelGetLength(self.p.handle, bass.BASS_POS_BYTE))

    #FIXME
    def getPosition(self):
        return bass.BASS_ChannelBytes2Seconds(self.p.handle, \
            bass.BASS_ChannelGetPosition(self.p.handle, bass.BASS_POS_BYTE)) \
            -self.p.cueChainStart
            
    def setPosition(self, pos):
        #CHECKME: from vb6 audica: "if we set position too intensively, it can block syncs"
        bass.BASS_ChannelSetPosition(self.p.handle, \
            bass.BASS_ChannelSeconds2Bytes(self.p.handle, pos + self.p.cueChainStart), \
            bass.BASS_POS_BYTE)
    
    #FIXME            
    def getLength(self):
        return self.p.timing
    
    def getStreamTags(self):
        with lock_tags:
            return tags.TAGS_Read(self.p.handle, "%UTF8(%ALBM\6%ARTI\6%CMNT\6%COMP\6%COPY\6%GNRE\6%TITL\6%TRCK\6%YEAR\6%SUBT\6%AART\6%DISC)".encode()).decode().split('\6')
            
    def getInfo(self):
        info = bass.BASS_CHANNELINFO()
        if bass.BASS_ChannelGetInfo(self.p.handle, info):
            return info
    
    def __resetPlayItem(self):
        self.p = PlayItem() #PlayItem dummy
    
    def close(self):
        """Close currently opened file"""
        if self.p.stream:
            bass.BASS_StreamFree(self.p.handle)
        else: bass.BASS_MusicFree(self.p.handle)
        self.__resetPlayItem()

    def __del__(self):
        self.close()
        
    def getLevel(self):
        return bass.BASS_ChannelGetLevel(self.p.handle)
        
    def getFloatData(self, ln):
        info = bass.BASS_CHANNELINFO()
        h = self.p.handle
        if bass.BASS_ChannelGetInfo(h, info):
            ln = ln*info.chans
            buf = (c_float*ln)()
            bass.BASS_ChannelGetData(h, byref(buf), \
                                    ln*4|bass.BASS_DATA_FLOAT)
            return buf, info.chans
            
    def getData(self):
        buf = (c_float*1024)()
        bass.BASS_ChannelGetData(self.p.handle, byref(buf), bass.BASS_DATA_FFT2048)
        return buf
        
    def getId3AlbumArt(self):
        #X0000000 X0000000 X0000000 X0000000 - X bits are ignored
        #High (0)      (1)      (2) Low  (3)
        def get28bitId3Size(cval):
            b3, b2, b1, b0 = map(lambda b: b & 0x7f, unpack("bbbb", cval))
            return (b3<<21)+(b2<<14)+(b1<<7)+b0
            
        def splitFlags(flags):
            "splits byte into bits and converts them to list of bools"
            return [bool(flags >> i & 1) for i in range(8)]
            
        def get_id3_apic():
            addr = bass.BASS_ChannelGetTags(self.p.handle, bass.BASS_TAG_ID3V2)
            if not addr: return
            reader = CTypesReader(addr)
            if reader.read(3) != "ID3": return #Check MAGIC
            major = ord(reader.read(1))
            if major > 4: return #Check major id3v2 version
            reader.read(1) #Skip revision number
            flags = ord(reader.read(1)) #unsync,extended header,experimental,0,0,0,0,0
            id3len = get28bitId3Size(reader.read(4))
            if not id3len: return
            if major == 3 and bool(flags&0b01000000): #extended header
                reader.read(10) #skip ex header
            elif major >= 4 and bool(flags&0b01000000): #extended header
                reader.read(get28bitId3Size(reader.read(4))) #skip ex header
            id3body = reader.read(id3len)
            if bool(flags&0b10000000): #remove unsynch. scheme (ff00xx > ffxx)
                id3body = id3body.replace("\xff\x00", "\xff")
            pos = 0
            while True: #skip frames until APIC
                if pos > id3len-4-4-2: return #id3 eof
                frame_name, pos = id3body[pos:pos+4], pos+4 #frame name
                #print frame_name
                if frame_name == "\0\0\0\0": return #padding area
                frame_len = unpack("!L",id3body[pos:pos+4])[0] if major != 4 \
                                    else get28bitId3Size(id3body[pos:pos+4])
                pos += 4 #Frame length field
                frame_hflags, pos = ord(id3body[pos+1:pos+2]), pos+2 #frame flags hi-byte
                if frame_hflags&1: #DLI - data length indicator
                    print("ID3v2: DLI detected!") #FIXME
                if frame_name == "APIC": break
                pos += frame_len
            frame_end_pos = frame_len + pos #End of APIC frame data
            #00 – ISO-8859-1 (Latin-1), 01 – UCS-2 (UTF-16 with BOM),
            #in ID3v2.2, 2.3, 02 – UTF-16BE without BOM in ID3v2.4,
            #03 – UTF-8 in ID3v2.4
            enc, pos = 0<ord(id3body[pos])<3, pos+1 #text encoding byte
            pos = id3body.find('\0', pos)+1 #skip MIME type
            if pos == 0: return
            pos += 1 #Skip picture type byte
            posT = id3body.find("\0\0" if enc else '\0', pos)
            if posT == -1: return
            if enc: #needs align if 16-bit encoding
                posT += 2 if (posT-pos)&1 else 1
            pos = posT + 1
            pixmap = QPixmap()
            pic_dat = id3body[pos:frame_end_pos] #pos = Start of picture data
            wr(r'c:\f1', id3body)
            wr(r'c:\f2', pic_dat)
            if pixmap.loadFromData(pic_dat):
                print("Album art loaded from ID3v2")
                return pixmap
            else: print("FAILED to load album art from ID3v2")

        def get_file_art(basenames):
            for i in basenames:
                for f in iglob(join(dirname(self.p.path), i+".*")):
                    if splitext(f)[1][1:] in P.COVER_EXTS \
                    and isfile(f):
                        art = QPixmap(f)
                        print("Album art loaded from %s file" % i)
                        return art
        
        return get_id3_apic() or get_file_art(P.COVER_FILES)
        
def volume(): return bass.BASS_GetVolume()
def setVolume(vol): bass.BASS_SetVolume(vol)
    
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

def init():
    sys.path.append("./bass")  # FIX: relative import in embedded pybass package
    global Filter
    bass.BASS_SetConfig(bass.BASS_CONFIG_DEV_DEFAULT, True) #follow default output device
    if not bass.BASS_Init(-1, 44100, 0, 0, 0):
        return False
    bass.BASS_SetConfig(bass.BASS_CONFIG_NET_PLAYLIST, 1) #enable playlist processing for i-net streams
    bass.BASS_SetConfig(bass.BASS_CONFIG_NET_PREBUF, 0) #minimize automatic pre-buffering, so we can do it (and display it) instead
    all_supp_exts = builtInFormats
    for f in glob.iglob(u"bass?*.dll"):
        plug = bass.BASS_PluginLoad(f, bass.BASS_UNICODE)
        if not plug: continue #not a plugin, skip
        Plugin_list[plug] = ({}, f) #init plugin in list
        pinfo = bass.BASS_PluginGetInfo(plug).contents
        #print pinfo.version
        for i in range(pinfo.formatc):
            info = pinfo.formats[i]
            if info.ctype == BASS_CTYPE_STREAM_MIDI: #load midi soundfont
                from bass import pybassmidi as bassmidi
                sf_h = bassmidi.BASS_MIDI_FontInit(MIDI_SOUNDFONT, bass.BASS_UNICODE)
                if sf_h:
                    font = bassmidi.BASS_MIDI_FONT(sf_h, -1) #, 0 - use default bank
                    bassmidi.BASS_MIDI_StreamSetFonts(0, font, 1)
                else: continue #do not include midi in supported files list
            Plugin_list[plug][0][info.ctype] = info.name.decode()
            exts = info.exts.decode().replace(";", " ")
            Filter.append(info.name.decode() + " (" + exts + ")")
            all_supp_exts += " " + exts     
    Filter = ";;".join(["All supported (" + all_supp_exts + ")"] + Filter)
    print("Plugins", Plugin_list)
    return True
    
def destroy():
    bass.BASS_Free()
    #bass.BASS_PluginFree(0)
        
def getFormatDesc(info):
    """translate a CTYPE value to text"""
    ctype = info.ctype
    if info.plugin in Plugin_list:
        descr = Plugin_list[info.plugin][0].get(ctype)
        if descr: return descr
        else: return "Unknown format "+Plugin_list[info.plugin][1]
    #built-in handlers
    if ctype & bass.BASS_CTYPE_STREAM: #HSTREAM flag
        if ctype == bass.BASS_CTYPE_STREAM_OGG: return "Ogg Vorbis"
        elif ctype == bass.BASS_CTYPE_STREAM_MP1: return "MPEG layer 1"
        elif ctype == bass.BASS_CTYPE_STREAM_MP2: return "MPEG layer 2"
        elif ctype == bass.BASS_CTYPE_STREAM_MP3: return "MPEG layer 3"
        elif ctype == bass.BASS_CTYPE_STREAM_AIFF: return "Audio IFF"
        elif ctype == bass.BASS_CTYPE_STREAM_CA: return "CoreAudio codec"
        elif ctype == bass.BASS_CTYPE_STREAM_MF: return "Media Foundation codec"
        elif ctype & bass.BASS_CTYPE_STREAM_WAV: #WAVE flag
            if ctype == bass.BASS_CTYPE_STREAM_WAV_PCM: return "PCM WAVE"
            elif ctype == bass.BASS_CTYPE_STREAM_WAV_FLOAT: return "Floating-point WAVE"
            else: return "WAVE"
    elif ctype & bass.BASS_CTYPE_MUSIC_MOD: #HMUSIC flag
        musicf = "MO3 " if ctype & bass.BASS_CTYPE_MUSIC_MO3 else ""
        ctype &= ~bass.BASS_CTYPE_MUSIC_MO3
        if ctype == bass.BASS_CTYPE_MUSIC_MTM: return musicf+"MultiTracker"
        elif ctype == bass.BASS_CTYPE_MUSIC_S3M: return musicf+"ScreamTracker 3"
        elif ctype == bass.BASS_CTYPE_MUSIC_XM: return musicf+"FastTracker 2"
        elif ctype == bass.BASS_CTYPE_MUSIC_IT: return musicf+"Impulse Tracker"
        else: return musicf+"Generic MOD"
    return "Unknown format"
    