# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 20:02:25 2021

@author: Андрей
"""

#from windows import itaskbarlist3
#exit()
from windows.com import Structure, POINTER, enum, create_instance_ex, S_OK
from windows.com import HWND, ULARGE_INTEGER, INT, UINT, DWORD, HICON, WCHAR, LPCWSTR, RECT
import ctypes
from ctypes import c_int,c_uint,c_short,c_ubyte,byref,Structure,oledll,c_long, \
                    POINTER, sizeof, windll, create_unicode_buffer, HRESULT
from ctypes.wintypes import HWND, ULARGE_INTEGER, INT, DWORD, UINT, \
                            HICON, WCHAR, LPCWSTR, RECT, BOOL, HBITMAP, LONG, \
                            WORD, LPVOID, POINT
ole32 = oledll.ole32
CLSCTX_INPROC_SERVER = 0x1
CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
IID_ITaskbarList3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"


class Guid(Structure):
    _fields_ = [("Data1", c_uint),
                ("Data2", c_short),
                ("Data3", c_short),
                ("Data4", c_ubyte*8)]
                
    def __init__(self, name):
        ole32.CLSIDFromString(unicode(name), byref(self))


def gen_method(ptr, method_index, *arg_types):
    c_long_p = POINTER(ctypes.c_int)
    vtable = ctypes.cast(ptr, c_long_p).contents.value
    print ptr, vtable
    def func(*args):
        WFC = ctypes.WINFUNCTYPE(HRESULT, c_long, *arg_types)
        METH = WFC(ctypes.cast(vtable + method_index*4, c_long_p).contents.value)
        return METH(ptr, *args)
    return func


def create_instance(clsid, iid):
    ptr = c_int()
    try:
        res = ole32.CoCreateInstance(byref(Guid(clsid)), 0, CLSCTX_INPROC_SERVER,
                                     byref(Guid(iid)), byref(ptr))
        if not res:
            return ptr.value
        else: return 0
    except: return 0


def create_instance_ex(obj, clsid, iid):
    "Creates an instance and generates methods"
    ptr = create_instance(clsid, iid)
    if ptr:
        for i in obj._methods_:
            setattr(obj, i[0], gen_method(ptr, i[1], *i[2]))
        obj.Release = gen_method(ptr, 2)
    else:
        print "CoCreateInstance failed"
    return ptr


class ITaskBarList3:
    _methods_ = ("SetProgressValue", 9, (HWND,ULARGE_INTEGER,ULARGE_INTEGER)), \
            ("SetProgressState", 10, (HWND,INT)), \
                
    def __init__(self):
        self.ptr = create_instance_ex(self, CLSID_TaskbarList, 
                                      IID_ITaskbarList3)
                               
    def __del__(self):
        if self.ptr:
            self.Release()
    
    def isAccessible(self):
        return bool(self.ptr)

from PyQt4 import QtGui as QtWidgets
class W(QtWidgets.QWidget):
    def __init__(self):
        super(W, self).__init__()
        self.bar = ITaskBarList3()

app = QtWidgets.QApplication([])
w = W()
w.show()
w.bar.SetProgressValue(int(w.winId()), 5, 10)
w.bar.SetProgressState(int(w.winId()), 4)
app.exec_()

# bar = ITaskBarList3()
# bar.SetProgressValue()
# input("?")
