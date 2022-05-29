# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 17:28:23 2013

@author: Winand
"""

from ctypes import c_ubyte
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.QtCore import QUrl, QThread
import timeit

class NetworkInit(QThread):
    """Don't know why but first network request is slow on my Win7x64sp1
    So init method should be called once on program start"""
    def __del__(self):
        self.wait()
    def run(self):
        QNetworkAccessManager().head(QNetworkRequest(QUrl("127.0.0.1")))
    @staticmethod
    def init():
        global ni_th
        if not 'ni_th' in globals():
            ni_th = NetworkInit()
            ni_th.start()

class ddict(dict):
    "dot notation dictionary"
    def __init__(self, **items):
        super(ddict, self).__init__(items)
    def __getattr__(self, attr):
        return self.get(attr, None)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

def HourMinSec(sec):
    m, s = divmod(round(sec), 60)
    if m < 60:
        return "%d:%02d" % (m,s)
    return "{0[0]}:{0[1]:02.0f}:{1:02.0f}".format(divmod(m,60), s)
#    h, (m, s) = 0, divmod(round(sec), 60)
#    if m >= 60:
#        h, m = divmod(m, 60)
#    return "%d:%02d:%02d" % (h, m, s) if h else "%d:%02d" % (m, s)
    
def s(prefix, text, suffix):
    '''returns <prefix><text><suffix> if text isn't empty
    otherwise returns empty string'''
    return "".join((prefix, text, suffix)) if text else ""
    
def sjoin(sep, *strings):
    "joins strings with sep, skips empty ones"
    return sep.join(filter(None, strings))
    
def overmind(obj):
    return super(type(obj), obj)
    
def bound(mn, v, mx):
    "bounds values"
    return max(min(mx, v), mn)
    
def isInside(pos, obj):
    "Checks if global pos is inside widget's rect"
    return obj.rect().contains(obj.mapFromGlobal(pos))
    
class CTypesReader():
    "Read data from memory address"
    def __init__(self, addr):
        self.addr = addr
        
    def read(self, ln):
        buf = (c_ubyte * ln).from_address(self.addr)
        self.addr += ln
        return str(bytearray(buf))

def wr(filename, dat):
    "simple way to put data to file"
    with file(filename, 'wb') as f:
        f.write(dat)

class FCollection_():
    def __init__(self):
        self.items = [] #data
        self.tblIdxLookup = {} #key->index
        self.tblKeyLookup = [] #index->key
        self.tblFreeKeys = [] #freed keys
    
    def append(self, v):
        if len(self.tblFreeKeys):
            k = self.tblFreeKeys.pop()
        else: k = len(self.tblKeyLookup)
        self.items.append(v)
        self.tblIdxLookup[k] = len(self.tblKeyLookup)
        self.tblKeyLookup.append(k)
        
    def __getitem__(self, idx):
        return self.items[idx]
        
    def __len__(self):
        return len(self.tblKeyLookup)
        
#    def get(self, idx):
#        return self.items[idx]
        
    def getByKey(self, key):
        return self.items[self.tblIdxLookup[key]]
        
    def remove(self, idx):
        #FIXME
        key = self.tblKeyLookup.pop(idx)
        del self.tblIdxLookup[key]
        self.tblFreeKeys.append(key)
        del self.items[idx]
        
    def removeByKey(self, key):
        #FIXME
        idx = self.tblIdxLookup.pop(key)
        del self.tblKeyLookup[idx]
        self.tblFreeKeys.append(key)
        del self.items[idx]
    
    def key(self, idx):
        return self.tblKeyLookup[idx]
                
    def index(self, key):
        return self.tblIdxLookup[key]   
        
    def exchange(self, idx1, idx2):
        key1, key2 = self.tblKeyLookup[idx1], self.tblKeyLookup[idx2]
        self.tblIdxLookup[key1], self.tblIdxLookup[key2] = idx2, idx1
        self.tblKeyLookup[idx1], self.tblKeyLookup[idx2] = key2, key1
        self.items[idx1], self.items[idx2] = self.items[idx2], self.items[idx1]
        
    def __getstate__(self):
        return self.items
        
    def __setstate__(self, state):
        self.items = state
        rg = xrange(len(state))
        self.tblIdxLookup, self.tblKeyLookup = {i:i for i in rg}, [i for i in rg]
        
    def sort(self, attr, down=True):
        print "..."
        res = sorted(range(len(self)), reverse=not down, \
            key=lambda i: attr(self[i]).lower())

class FCollection():    
    def __init__(self):
        self.setItems([])
        
    def sort(self, attr, order, sel):
#        sort_idxs = sorted(range(len(self.items)), reverse=order==1, \
#            key=lambda i: attr(self.items[i]).lower())
#        temp = []
#        for i in sort_idxs:
#            temp.append(self.items[i])
#        self.items = temp
#        print sort_idxs
        
#        f = self.items[5]
#        tmp = sorted(enumerate(self.items), reverse=order==1, \
#            key=lambda i: attr(i[1]).lower())
#        idxs, self.items = zip(*tmp)
#        print self.items.index(f)
        
        a=timeit.default_timer()
        sort = sorted(self.items, reverse=order==1, key=lambda i: attr(i))
        self.setItems(sort)
        print timeit.default_timer()-a, len(sort)
#        fsel = [False]*len(self)
#        for i in sel:
#            fsel[i] = True
#        sitems = zip(self.items, fsel)
#        sort, fsel = zip(*sorted(sitems, reverse=order==1, key=lambda i: attr(i[0]).lower()))
#        self.setItems(sort)
#        return [i for i, j in enumerate(fsel) if j == True]

    def setFilter(self, text, *attrs):
        if not text: #unfilter
            self.items = self.full_items
            return
            
        def find(item):
            for i in attrs:
                if ltext in i(item).lower():
                    return True
        ltext = text.lower()
        self.items = filter(find, self.full_items)
        self.filter = {"text": text, "attrs": attrs}
        
    def __getstate__(self):
        return self.full_items #return full item list
        
    def __setstate__(self, state):
        #print state
        self.setItems(state)
        
    def __len__(self):
        return len(self.items)
        
    def __getitem__(self, idx):
        return self.items[idx]
        
    def setItems(self, items):
        self.items = items #currently viewed data
        self.full_items = self.items #save items when filtering
        
    def append(self, v):
        if self.items == self.full_items:
            self.items.append(v)
        else:
            self.full_items.append(v)
            self.setFilter(self.filter["text"], self.filter["attrs"])
        
#fc = FCollection()
#
#fc.add("along")
#fc.add("comes")
#fc.add("Mary")
#key = fc.key(1)
#fc.removeByKey(key)
#print fc.get(1)
