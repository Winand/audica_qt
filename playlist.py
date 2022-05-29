# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 17:16:44 2013

@author: Winand
"""

import struct, cStringIO
from PyQt4.QtGui import QStandardItem, QStandardItemModel, QBrush, QColor, \
    QStyledItemDelegate, QSortFilterProxyModel, QStyle, QPalette
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt
from PyQt4.QtGui import QItemSelectionModel, QItemSelection
from general import HourMinSec, s, sjoin, FCollection, overmind
import cPickle, zipfile
selectionModel = None

#def cs(s):
#    return s.encode('cp1251', 'ignore')

class DoubleColumn(QStyledItemDelegate):
    def paint(self, painter, option, index):
        overmind(self).paint(painter, option, index)
        item = index.model().items[index.row()]
        if option.state & QStyle.State_Enabled:
            if option.state & QStyle.State_Active:
                cg = QPalette.Normal
            else: cg = QPalette.Inactive
        else: cg = QPalette.Disabled
        painter.setPen(option.palette.color(cg, \
            QPalette.HighlightedText if option.state & QStyle.State_Selected \
            else QPalette.Text \
        ))
        painter.drawText(option.rect.adjusted(5,1,0,0), Qt.AlignLeft|Qt.AlignVCenter, item.Track)
        painter.drawText(option.rect.adjusted(0,1,-5,0), Qt.AlignRight|Qt.AlignVCenter, item.l_timing)

class PlayListModelFS(QSortFilterProxyModel):
    def __init__(self, model, parent=None):
        overmind(self).__init__(parent)
        self.setSourceModel(model)
        self.Title = model.Title
        self.items = model.items
        self.filter_mask = ""
        self.attrs_filt = (PlayItem.sort_song, PlayItem.sort_artist, \
                                    PlayItem.filt_album, PlayItem.sort_path)
        
    def setFilter(self, text):
        self.filter_mask = text.lower()
        self.invalidateFilter()
        
    def filterAcceptsRow(self, source_row, source_parent):
        item = self.items[source_row]
        for i in self.attrs_filt:
            if self.filter_mask in i(item):
                return True
        return False
        
    def sort(self, column, order):
        self.sourceModel().sort(column, order)
        
#    def lessThan(self, left, right):
#        it1, it2 = self.items[left.row()], self.items[right.row()]
#        attr = self.attrs_sort[left.column()]
#        return attr(it1).lower() < attr(it2).lower()
        
        
#    def setFilterMinimumDate(self, date):
#        self.minDate = date
#        self.invalidateFilter()

#    def filterAcceptsRow(self, sourceRow, sourceParent):
#        index0 = self.sourceModel().index(sourceRow, 0, sourceParent)
#        index1 = self.sourceModel().index(sourceRow, 1, sourceParent)
#        index2 = self.sourceModel().index(sourceRow, 2, sourceParent)
#
#        return (   (self.filterRegExp().indexIn(self.sourceModel().data(index0)) >= 0
#                    or self.filterRegExp().indexIn(self.sourceModel().data(index1)) >= 0)
#                and self.dateInRange(self.sourceModel().data(index2)))

#    def lessThan(self, left, right):
#        leftData = self.sourceModel().data(left)
#        rightData = self.sourceModel().data(right)
#        print leftData,rightData,left,right
#
#        if not isinstance(leftData, QtCore.QDate):
#            emailPattern = QtCore.QRegExp("([\\w\\.]*@[\\w\\.]*)")
#
#            if left.column() == 1 and emailPattern.indexIn(leftData) != -1:
#                leftData = emailPattern.cap(1)
#
#            if right.column() == 1 and emailPattern.indexIn(rightData) != -1:
#                rightData = emailPattern.cap(1)
#
#        return leftData < rightData

class PlayListModel(QAbstractTableModel):
    def __init__(self, parent=None, *args): 
        overmind(self).__init__(parent, *args) 
        self._columnCount = 4
        self.items = FCollection()
        self.Title = ""
        self.chooseMethod = 0
        self.playing = None
        self.next = None
 
    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.items)
        return 0
        
    def columnCount(self, parent=QModelIndex()): 
        return self._columnCount
 
    def data(self, index, role):
        #print index.row()
        if not index.isValid(): return QVariant()
        row = index.row()
        if row > len(self.items): return QVariant()
        if role == Qt.DisplayRole:
            column = index.column()
            item = self.items[row]
            if column == 0:
                return (item.Station if item.remote else item.Song) or item.path
            elif column == 1:
                return item.Website or item.file if item.remote else \
                                    item.Artist if item.gotTags else QVariant()
            elif column == 2:
                if item.gotTags and not item.remote:
                    return item.l_Album
#            elif column == 3:
#                if item.gotTags and not item.remote:
#                    return item.Track + "\t" + item.l_timing
#            elif column == 4:
#                if item.gotTags and not item.invalid:
#                    return item.l_timing
#                if item.remote: return "i"
        elif role == Qt.ForegroundRole:
            if row == 2:
                return QBrush(QColor(Qt.red))
#        elif role == Qt.BackgroundRole:
#            if row % 2:
#                return QBrush(QColor("#fafafa"))
        elif role == Qt.ToolTipRole:
            item = self.items[row]
            return sjoin("\r\n", sjoin(" - ", item.Artist, item.Song),
                         sjoin(", ", item.l_timing, item.Album, item.Year))
        #elif role == Qt.TextAlignmentRole:
        #    return Qt.AlignJustify
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return
        if section == 0:
            return "Song"
        elif section == 1:
            return "Artist"
        elif section == 2:
            return "Album"
        elif section == 3:
            return "By path"
        return "<Unknown>"

#    def qsort(self):
#        def qsort_int(first, last):
#            low, mid, high = first, self.items[(first+last)//2].Song.lower(), last
#            while True:
#                while True:
#                    if cmp(self.items[low].Song.lower(), mid) == -1: low += 1
#                    else: break
#                while True:
#                    if cmp(self.items[high].Song.lower(), mid) == 1: high -= 1
#                    else: break
#                if low <= high:
#                    if low < high:
#                        self.items.exchange(low, high)
#                    low += 1
#                    high -= 1
#                if low > high: break
#            return [(low, last), (first, high)]
#            
#        stack = qsort_int(0, len(self.items)-1)
#        while len(stack):
#            context = stack.pop()
#            if context[0] < context[1]:
#                stack += qsort_int(context[0], context[1])
        
    def sort(self, column, order = Qt.AscendingOrder):
#        isel, rsel = selectionModel.selectedRows(), []
#        if isel and len(isel):
#            rsel = [i.row() for i in isel]
        sort_arg = (PlayItem.sort_song, PlayItem.sort_artist, \
                            PlayItem.sort_album, PlayItem.sort_path)[column]
        self.items.sort(sort_arg, order, None)
#        selectionModel.clear()
#        selection = QItemSelection()
#        for i in rsel2:
#            idx = self.index(i, 0)
#            selection.select(idx, idx)
#        selectionModel.select(selection, QItemSelectionModel.Rows|QItemSelectionModel.Select)
        self.layoutChanged.emit()
        
    def supportedDropActions(self): 
        return Qt.CopyAction | Qt.MoveAction

    def flags(self, index):
        if index.isValid(): 
            return Qt.ItemIsSelectable|Qt.ItemIsDragEnabled|Qt.ItemIsEnabled
        return Qt.ItemIsSelectable|Qt.ItemIsDragEnabled| \
                    Qt.ItemIsDropEnabled|Qt.ItemIsEnabled

    def dropMimeData(self, data, action, row, column, parent):
        print 'dropMimeData %s %s %s %s' % (data.data('text/xml'), action, row, parent)
        print parent.model().items[parent.row()]
        return True
        
    def setFilter(self, text):
        self.items.setFilter(text, PlayItem.sort_song, PlayItem.sort_artist, \
                                    PlayItem.filt_album, PlayItem.sort_path)
        self.layoutChanged.emit()
            
class PlayItem(object):
    VERSION = 77 #check if we load (unpickle) right version of class
    
    m_timing = 0
    l_timing = ''
    offset = 0
    length = 0
    cueChainStart = 0
    path = ''
    Artist = ''
    Song = ''
    Year = ''
    m_Album = ''
    l_Album = ''
    Track = ''
    #Radio
    Website = ''
    Station = ''
    #flags
    gotTags=invalid=remote=noChains=isCueLink=False
    @property
    def timing(self): return self.m_timing
    @timing.setter
    def timing(self, sec):
        self.m_timing = sec
        self.l_timing = HourMinSec(sec)
    @property
    def Album(self): return self.m_Album
    @Album.setter
    def Album(self, album):
        self.m_Album = album
        self.l_Album = sjoin(" ", album, s("(", self.Year, ")"))
    
    def __getstate__(self):
        remote = self.remote
        return (self.VERSION, remote, self.gotTags, self.invalid, \
                self.noChains, self.isCueLink) + \
                ((self.Website, self.Station) if remote else \
                (self.timing, self.offset, self.length, self.cueChainStart, \
                self.Artist, self.Song, self.Year, self.Album, self.Track)) + \
                (self.path,)
        
    def __setstate__(self, state):
        ver, remote = state[:2]
        if ver == 77:
            if remote:
                self.gotTags, self.invalid, self.noChains, self.isCueLink, \
                self.Website, self.Station, self.path = state[2:]
            else:
                self.gotTags, self.invalid, self.noChains, self.isCueLink, \
                self.timing, self.offset, self.length, self.cueChainStart, \
                self.Artist, self.Song, self.Year, self.Album, self.Track, \
                self.path = state[2:]

    def format_track(self):
        p = self.Track.find("/")
        if p==-1: p = self.Track.find("\\")
        if p==-1: return self.Track.rjust(4, '0')
        return self.Track[:p].rjust(4, '0')
    
    def sort_song(self): return self.Song.lower()
    def sort_artist(self): return self.Artist.lower()
    def sort_album(self): return (self.m_Album+self.format_track()).lower()
    def filt_album(self): return self.m_Album.lower()
    def sort_path(self): return self.path.lower()

class PlaylistSet():
    MAGIC_PL = "AU$"
    
    def __init__(self, lists=()):
        self.lists = lists
    
    def readString(self, dat):
        "read utf-16 string at position"
        ln, = struct.unpack('<H', dat.read(2))
        return unicode(dat.read(ln), 'utf-16')
        
    def readStrings(self, dat, num):
        "read specified amount of utf-16 strings at position"
        return [unicode(dat.read( \
            struct.unpack('<H', dat.read(2))[0]), 'utf-16') \
            for i in range(num)]
        
    def splitFlags(self, flags):
        "splits byte into bits and converts them to list of bools"
        return [bool(flags >> i & 1) for i in range(8)]
    
    #old format ===>
    def loadv75(self, dat):
        listCount = ord(dat.read(1))
        print listCount
        lists = [PlayListModel() for i in range(listCount)]
        for i in xrange(listCount):
            lists[i].Title = self.readString(dat)
            #True=rnd,False=linear
            lists[i].chooseMethod, lists[i].playing = \
                struct.unpack('<?L', dat.read(1+4))
            while True:
                pi = PlayItem()
                pi.gotTags, pi.invalid, pi.remote, stop, \
                    pi.noChains, pi.isCueLink, x, x = \
                    self.splitFlags(ord(dat.read(1)))
                if stop: break
                if pi.remote:
                    pi.Website, pi.Station = self.readStrings(dat, 2)
                else:
                    pi.timing, pi.offset, pi.length, pi.cueChainStart = \
                        struct.unpack('<fLLf', dat.read(4*4))
                    pi.Artist, pi.Song, pi.Year, pi.Album, pi.Track = \
                        self.readStrings(dat, 5)
                pi.path = self.readString(dat)
                lists[i].items.append(pi)
        return lists
        
    def loadOldFormat(self, filepath):
        try:
            dat = cStringIO.StringIO(file(filepath, 'rb').read())
            magic_len = len(self.MAGIC_PL)
            #if len(dat) <= magic_len: return False #short file
            if str(dat.read(magic_len)) != self.MAGIC_PL: return False #unrecognized filetype
            loader = getattr(self, "loadv"+str(ord(dat.read(1))), None)
            if loader: return loader(dat) #load recognized playlist ver
        except:
            print "Wrong old format playlist"
            return tuple()
    #<=== old format
    
    def load(self, filepath):
#        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                dat = cPickle.loads(zf.read('playlist'))
                lists = [PlayListModel() for i in range(len(dat))]
                for i in range(len(lists)):
                    lists[i].Title = dat[i][0]
                    lists[i].chooseMethod = dat[i][1]  
                    lists[i].playing = dat[i][2]
                    lists[i].items = dat[i][3]
                self.lists = [PlayListModelFS(i) for i in lists]#lists
#        except zipfile.BadZipfile:
#            self.lists = self.loadOldFormat(filepath)
#        except:
#            print "Playlist load error"
#            self.lists = ()
            return self.lists
    
    def save(self, filepath):
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            dat = [(l.Title, l.chooseMethod, l.playing, l.items) \
                for l in self.lists]
            zf.writestr('playlist', cPickle.dumps(dat, -1))


#PlaylistSet().load(r'lst.aupx')
#print len(PlaylistSet().load(r'lst.aupx'))
#    PLAYLISTVER = 76
#    def writeStringArray(self, f, *strings):
#        f.write(chr(len(strings)))
#        utf8s = [s.encode('utf-8') for s in strings]
#        f.write(struct.pack('!'+'H'*len(utf8s), *[len(s) for s in utf8s]))
##        for s in utf8s:
##            f.write(s)
#        f.write("".join(utf8s))
#            
#    def writeString(self, f, string):
#        utf8s = string.encode('utf-8')
#        f.write(struct.pack('!H', len(utf8s)) + utf8s)
#        
#    def readString8(self, dat):
#        "read utf-8 string at position"
#        ln, = struct.unpack('!H', dat.read(2))
#        return unicode(dat.read(ln), 'utf-8')
#            
#    def readStringArray(self, dat):
#        ln = ord(dat.read(1))
#        lens = struct.unpack('!'+'H'*ln, dat.read(ln*2))
#        return [unicode(dat.read(lens[i]), 'utf-8') for i in range(ln)]
#        
#    def serializeFlags(self, *flags):
#        "serialize up to 8 flags into one byte"
#        return reduce(lambda acc, i: \
#                        acc + (int(flags[i])<<i), range(min(8,len(flags))), 0)            
#    def loadv76(self, dat):
#        listCount = ord(dat.read(1))
#        lists = [PlayListModel() for i in range(listCount)]
#        for l in lists:
#            l.Title = self.readString8(dat)
#            ln, l.chooseMethod, l.playing = struct.unpack('!L?L', dat.read(4+1+4))
#            for ii in xrange(ln):
#                pi = PlayItem()
#                pi.gotTags, pi.invalid, pi.remote, pi.noChains, pi.isCueLink, \
#                                    x, x, x = self.splitFlags(ord(dat.read(1)))
#                if pi.remote:
#                    pi.Website, pi.Station, pi.path = self.readStringArray(dat)
#                else:
#                    pi.timing, pi.offset, pi.length, pi.cueChainStart = \
#                            struct.unpack('!fLLf', dat.read(4*4))
#                    pi.Artist, pi.Song, pi.Year, pi.Album, pi.Track, pi.path = \
#                                        self.readStringArray(dat)
#                l.items.append(pi)
#        return lists
#            
#    def savev76(self, filepath, lists):
#        f = file(filepath, 'wb')
#        f.write(self.MAGIC_PL + chr(self.PLAYLISTVER))
#        f.write(chr(len(lists)))
#        for l in lists:
#            self.writeString(f, l.Title)
#            f.write(struct.pack('!L?L', len(l.items), l.chooseMethod, l.playing))
#            for pi in l.items:
#                f.write(chr(self.serializeFlags(pi.gotTags, pi.invalid, \
#                                        pi.remote, pi.noChains, pi.isCueLink)))
#                if pi.remote:
#                    self.writeStringArray(f, pi.Website, pi.Station, pi.path)
#                else:
#                    f.write(struct.pack('!fLLf', \
#                            pi.timing, pi.offset, pi.length, pi.cueChainStart))
#                    self.writeStringArray(f, pi.Artist, pi.Song, pi.Year, \
#                                                pi.Album, pi.Track, pi.path)
#        f.close()

#class bytearr(bytearray):
#    "bytearray with serial read capability"
#    def __init__(self, *args, **kwargs):
#        super(bytearr, self).__init__(*args, **kwargs)
#        self.pos = 0
#        
#    def read(self, ln):
#        pos_o = self.pos
#        self.pos += ln
#        return self[pos_o:self.pos]