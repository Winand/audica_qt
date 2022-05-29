# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 19:16:37 2013

@author: Winand
"""

from PyQt5 import QtCore, QtGui
import ctypes
from ctypes import c_int,c_uint,c_short,c_ubyte,byref,Structure,oledll,c_long, \
                    POINTER, sizeof, windll, create_unicode_buffer
from ctypes.wintypes import HWND, ULARGE_INTEGER, INT, DWORD, UINT, \
                            HICON, WCHAR, LPCWSTR, RECT, BOOL, HBITMAP, LONG, \
                            WORD, LPVOID, POINT
from ctypes import HRESULT
CLSCTX_INPROC_SERVER = 0x1
S_OK = 0
#from _ctypes import call_commethod
ole32 = oledll.ole32

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
    def func(*args):
        return ctypes.WINFUNCTYPE(HRESULT, c_long, *arg_types)(
            ctypes.cast(vtable + method_index*4, c_long_p).contents.value)(
            ptr, *args)
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
    else: print("CoCreateInstance failed")
    return ptr
    
def enum(**enums):
    "usage: x=enum(a=1,b=2,c=4,)"
    return type('Enum', (), enums)
    
#class ICONINFO(Structure):
#    _fields_ = [("fIcon", BOOL),
#                ("xHotspot", DWORD),
#                ("yHotspot", DWORD),
#                ("hbmMask", HBITMAP),
#                ("hbmColor", HBITMAP)]
#                
#class BITMAP(Structure):
#    _fields_ = [("bmType", LONG),
#                ("bmWidth", LONG),
#                ("bmHeight", LONG),
#                ("bmWidthBytes", LONG),
#                ("bmPlanes", WORD),
#                ("bmBitsPixel", WORD),
#                ("bmBits", LPVOID)]
#                
#ii = ICONINFO()
#bm = BITMAP()
#if windll.user32.GetIconInfo(pr,byref(ii)):
#    if ii.hbmColor:
#        if windll.gdi32.GetObjectA(ii.hbmColor, sizeof(BITMAP), byref(bm)):
#            w = bm.bmWidth
#            h = bm.bmHeight
#            d = bm.bmBitsPixel
#        windll.gdi32.DeleteObject(ii.hbmColor)
#    elif windll.gdi32.GetObjectA(ii.hbmMask, sizeof(BITMAP), byref(bm)):
#            w = bm.bmWidth
#            h = bm.bmHeight
#            d = bm.bmBitsPixel
#    windll.gdi32.DeleteObject(ii.hbmMask)
#print "icoinf", w,h,d

#Windows 7 colorization
class WDM_COLORIZATION_PARAMS(Structure):
    _fields_ = [("Color", LONG),
                ("Afterglow", LONG),
                ("ColorBalance", LONG),
                ("AfterglowBalance", LONG),
                ("BlurBalance", LONG),
                ("GlassReflectionIntensity", LONG),
                ("Opaque", LONG)]
        
DwmGetColorizationParameters = windll.dwmapi[127] #(WDM_COLORIZATION_PARAMS* p)

DwmSetColorizationParameters = windll.dwmapi[131] #(WDM_COLORIZATION_PARAMS* p, LONG uUnknown)
def DwmSetColorizationParametersEx(color):
    "Wrapper for setting color easily, returns old color"
    wdm_c_par=WDM_COLORIZATION_PARAMS()
    if not DwmGetColorizationParameters(byref(wdm_c_par)):
        prevColor = wdm_c_par.Color
        wdm_c_par.Color = color
        wdm_c_par.Afterglow = color
        if DwmSetColorizationParameters(byref(wdm_c_par),0) == 0:
            return prevColor
    return False

#oldcol = DwmSetColorizationParametersEx(0xff0000)
#raw_input()
#if oldcol:
#    DwmSetColorizationParametersEx(oldcol)

def GetKeyboardLayoutName():
    LOCALE_SISO639LANGNAME = 89
    buf = create_unicode_buffer(3)
    langId = windll.user32.GetKeyboardLayout(0) & 0xffff
    windll.kernel32.GetLocaleInfoW(langId, LOCALE_SISO639LANGNAME, buf, len(buf))
    return buf.value.title()
    
class WINDOWPOS(ctypes.Structure):
    _fields_ = [
        ('hwnd', ctypes.c_ulong),
        ('hwndInsertAfter', ctypes.c_ulong),
        ('x', ctypes.c_int),
        ('y', ctypes.c_int),
        ('cx', ctypes.c_int),
        ('cy', ctypes.c_int),
        ('flags', ctypes.c_ulong)
    ]
    
WM_WINDOWPOSCHANGING = 0x46 #Sent to a window whose size, position, or place in the Z order is about to change

WM_DEVICECHANGE = 0x219 #Notifies an application of a change to the hardware configuration of a device or the computer.
DBT_DEVICEARRIVAL = 0x8000 #A device or piece of media has been inserted and is now available.
DBT_DEVICEREMOVECOMPLETE = 0x8004 #A device or piece of media has been removed.
class DEV_BROADCAST_HDR (Structure):
  _fields_ = [
    ("dbch_size", DWORD),
    ("dbch_devicetype", DWORD),
    ("dbch_reserved", DWORD)
  ]
DBT_DEVTYP_VOLUME = 2 #Logical volume
class DEV_BROADCAST_VOLUME (Structure):
  _fields_ = [
    ("dbcv_size", DWORD),
    ("dbcv_devicetype", DWORD),
    ("dbcv_reserved", DWORD),
    ("dbcv_unitmask", DWORD),
    ("dbcv_flags", WORD)
  ]
GetDriveType = windll.kernel32.GetDriveTypeA #Checks if a disk drive is a removable, fixed, CD-ROM, RAM disk, or network drive.
DRIVE_REMOVABLE = 2
DRIVE_CDROM = 5
def isFloppyDrive(letter):
    #maybe not completely correct technique
    buf = create_unicode_buffer(1024)
    windll.kernel32.QueryDosDeviceW(letter+u':', buf, len(buf))
    return buf.value.startswith('\Device\Floppy') #\Device\Imdisk
def getVolumeInformation(letter):
    buf = create_unicode_buffer(261)
    vserial = DWORD()
    windll.kernel32.GetVolumeInformationW(letter+u':\\', buf, len(buf), byref(vserial),0,0,0,0)
    return buf.value, vserial.value
    
SetCurrentProcessExplicitAppUserModelID = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
