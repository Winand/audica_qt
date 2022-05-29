# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 19:21:30 2013

@author: Winand
"""

from general import overmind
from PyQt4.QtCore import QAbstractEventDispatcher, pyqtSignal, QObject
from PyQt4.QtGui import QPixmap
from com import Structure, POINTER, enum, create_instance_ex, S_OK
from com import HWND, ULARGE_INTEGER, INT, UINT, DWORD, HICON, WCHAR, LPCWSTR, RECT
HIMAGELIST = HICON #c_void_p handle ?
WM_COMMAND = 0x0111
CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
IID_ITaskbarList3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"

THBN_CLICKED = 0x1800
WM_DWMSENDICONICTHUMBNAIL = 0x323

THUMBBUTTONMASK = enum(
    THB_BITMAP = 1,
    THB_ICON = 2,
    THB_TOOLTIP = 4,
    THB_FLAGS = 8,
)
THBMASK = THUMBBUTTONMASK
TBPFLAG = enum(
    TBPF_NOPROGRESS = 0,
    TBPF_INDETERMINATE = 1,
    TBPF_NORMAL = 2,
    TBPF_ERROR = 4,
    TBPF_PAUSED = 8,
)
class THUMBBUTTON(Structure):
    _fields_ = [("dwMask", INT),
                ("iId", UINT),
                ("iBitmap", UINT),
                ("hIcon", HICON),
                ("szTip", WCHAR*260),
                ("dwFlags", INT)]

class ITaskBarList3(QObject):
    buttonPress = pyqtSignal(int)
    _methods_ = ("SetProgressValue", 9, (HWND,ULARGE_INTEGER,ULARGE_INTEGER)), \
            ("SetProgressState", 10, (HWND,INT)), \
            ("RegisterTab", 11, (HWND,HWND)), \
            ("UnregisterTab", 12, (HWND,)), \
            ("SetTabOrder", 13, (HWND,HWND)), \
            ("SetTabActive", 14, (HWND,HWND,DWORD)), \
            ("_ThumbBarAddButtons", 15, (HWND,UINT,POINTER(THUMBBUTTON))), \
            ("ThumbBarUpdateButtons", 16, (HWND,UINT,POINTER(THUMBBUTTON))), \
            ("ThumbBarSetImageList", 17, (HWND,HIMAGELIST)), \
            ("SetOverlayIcon", 18, (HWND,HICON,LPCWSTR)), \
            ("SetThumbnailTooltip", 19, (HWND,LPCWSTR)), \
            ("SetThumbnailClip", 20, (HWND,POINTER(RECT))), \
#            ITaskbarList4 methods
#            STPFLAG = enum(
#                STPF_NONE = 0,
#                STPF_USEAPPTHUMBNAILALWAYS = 0x1,
#                STPF_USEAPPTHUMBNAILWHENACTIVE = 0x2,
#                STPF_USEAPPPEEKALWAYS = 0x4,
#                STPF_USEAPPPEEKWHENACTIVE = 0x8,
#            )            
#            ("SetTabProperties", 21, (HWND,STPFLAG)), \
                
    def __init__(self, widget):
        overmind(self).__init__()
        self.hwnd = int(widget.winId())
#        from ctypes import windll
#        DWMWA_HAS_ICONIC_BITMAP = 0xa
#        DWMWA_FORCE_ICONIC_REPRESENTATION = 0x7
#        DwmSetWindowAttribute = windll.dwmapi.DwmSetWindowAttribute
#        DwmSetWindowAttribute(self.hwnd,DWMWA_HAS_ICONIC_BITMAP,1,4)
#        DwmSetWindowAttribute(self.hwnd,DWMWA_FORCE_ICONIC_REPRESENTATION,1,4)
#        DwmInvalidateIconicBitmaps = windll.dwmapi.DwmInvalidateIconicBitmaps
#        DwmInvalidateIconicBitmaps(self.hwnd)
        self.ptr = create_instance_ex(self, CLSID_TaskbarList, 
                                      IID_ITaskbarList3)
                               
    def __del__(self):
        if self.ptr:
            self.Release()
    
    def isAccessible(self):
        return bool(self.ptr)
    
    def ThumbBarAddButtons(self, icons):
        QAbstractEventDispatcher.instance().setEventFilter(self.eventFilter)
        icons, strTips = zip(*icons)
        icons = map(QPixmap.toWinHICON, icons) #FIXME: resources are not controlled
        buttons = (THUMBBUTTON * len(icons))()
        for i, v in enumerate(icons):
            buttons[i].dwMask = THBMASK.THB_ICON|THBMASK.THB_TOOLTIP
            buttons[i].iId = i
            #buttons[i].iBitmap = 0
            buttons[i].hIcon = int(v)
            buttons[i].szTip = strTips[i] + u'\0'
            #buttons[i].dwFlags = 0
        return self._ThumbBarAddButtons(self.hwnd, len(icons), buttons[0]) == S_OK
        
    def eventFilter(self, message):
        if message.message == WM_COMMAND:  
            if int(message.hwnd) == self.hwnd and \
            message.wParam >> 16 == THBN_CLICKED:
                self.buttonPress.emit(message.wParam & 0xffff)
                print "+"
        elif message.message == WM_DWMSENDICONICTHUMBNAIL:
            print "iconic"
#        register message first: WA_TASKBARCREATED = windll.user32.RegisterWindowMessageA("TaskbarButtonCreated")
#        elif message.message == WA_TASKBARCREATED:
#            print "WA_TASKBARCREATED"
        return False


#from ctypes import windll
#LoadImage = windll.user32.LoadImageW
#IMAGE_ICON = 1
#LR_LOADFROMFILE = 0x00000010
#LR_DEFAULTSIZE = 0x00000040
#LR_SHARED = 0x00008000
#pr = HICON(LoadImage(0, u'../res/win_taskbar_prev2.ico', IMAGE_ICON, 0, 0, LR_LOADFROMFILE|LR_SHARED))
#ps = HICON(LoadImage(0, u'../res/win_taskbar_pause.ico', IMAGE_ICON, 0, 0, LR_LOADFROMFILE|LR_SHARED))
#nx = HICON(LoadImage(0, u'../res/win_taskbar_next2.ico', IMAGE_ICON, 0, 0, LR_LOADFROMFILE|LR_SHARED))
#pl = HICON(LoadImage(0, u'../res/win_taskbar_play1.ico', IMAGE_ICON, 0, 0, LR_LOADFROMFILE|LR_SHARED))

#from com import WDM_COLORIZATION_PARAMS, byref, DwmGetColorizationParameters, DwmSetColorizationParameters
#wdm_c_par=WDM_COLORIZATION_PARAMS()
#print DwmGetColorizationParameters(byref(wdm_c_par))
##wdm_c_par.Color1 = (wdm_c_par.Color1 & 0xff000000)|0xff0000
##wdm_c_par.Color2 = wdm_c_par.Color1
#print wdm_c_par.Color1 & 0xffffff, wdm_c_par.Color2 & 0xffffff, wdm_c_par.Color1 & 0xff000000, wdm_c_par.Color2 & 0xff000000
#wdm_c_par.Opaque=0
#print DwmSetColorizationParameters(byref(wdm_c_par),0)
##print wdm_c_par.Color1 >> 24, wdm_c_par.Color1 & 0xffffff
#
#WA_TASKBARCREATED = windll.user32.RegisterWindowMessageA("TaskbarButtonCreated")
#
#import PyQt4.QtGui, sys
#class mainWnd(PyQt4.QtGui.QMainWindow):
#    WM_COMMAND = 0x0111
#    def winEvent(self, message):
#        if message.message == self.WM_COMMAND:
#            if message.wParam >> 16 == THBN_CLICKED:
#                print message.wParam & 0xffff
##        elif message.message == WA_TASKBARCREATED:
##            print "WA_TASKBARCREATED"
#        elif message.message == WM_DWMSENDICONICTHUMBNAIL:
#            print "iconic"
#        return PyQt4.QtGui.QMainWindow.winEvent(self, message)
#        
#app = PyQt4.QtGui.QApplication(sys.argv)
#mainwnd = mainWnd()
#mainwnd.show()
#wnd = int(mainwnd.winId())
#
#taskbar = ITaskBarList3()
#taskbar.SetProgressValue(wnd, 5, 10)
#taskbar.SetProgressState(wnd, TBPFLAG.TBPF_ERROR)
#pr = QPixmap('../res/win_taskbar_prev2.ico')
#ps = QPixmap('../res/win_taskbar_pause.ico')
#nx = QPixmap('../res/win_taskbar_next2.ico')
#pl = QPixmap('../res/win_taskbar_play1.ico')
#icons = (pr, ps, nx,)
#tips = (u"Previous", u"Play", u"Next")
#taskbar.ThumbBarAddButtons(wnd, icons, tips)
#taskbar.SetOverlayIcon(wnd, int(pl.toWinHICON()), u'Oh, wow')
#taskbar.SetThumbnailTooltip(wnd, u'Oh, just wow')
#del taskbar
#
#ret = app.exec_()
#del app


import PyQt4.QtGui, sys
class mainWnd(PyQt4.QtGui.QMainWindow):
    WM_COMMAND = 0x0111
    def winEvent(self, message):
        if message.message == self.WM_COMMAND:
            if message.wParam >> 16 == THBN_CLICKED:
                print message.wParam & 0xffff
#        elif message.message == WA_TASKBARCREATED:
#            print "WA_TASKBARCREATED"
        elif message.message == WM_DWMSENDICONICTHUMBNAIL:
            print "iconic"
        return PyQt4.QtGui.QMainWindow.winEvent(self, message)
        
app = PyQt4.QtGui.QApplication(sys.argv)
mainwnd = mainWnd()
mainwnd.show()
wnd = int(mainwnd.winId())

taskbar = ITaskBarList3(mainwnd)
taskbar.SetProgressValue(wnd, 5, 10)
taskbar.SetProgressState(wnd, TBPFLAG.TBPF_ERROR)
#pr = QPixmap('../res/win_taskbar_prev2.ico')
#ps = QPixmap('../res/win_taskbar_pause.ico')
#nx = QPixmap('../res/win_taskbar_next2.ico')
#pl = QPixmap('../res/win_taskbar_play1.ico')
#icons = (pr, ps, nx,)
#tips = (u"Previous", u"Play", u"Next")
#taskbar.ThumbBarAddButtons(zip(icons, tips))
#taskbar.SetOverlayIcon(wnd, int(pl.toWinHICON()), u'Oh, wow')
#taskbar.SetThumbnailTooltip(wnd, u'Oh, just wow')
#del taskbar

ret = app.exec_()
del app
