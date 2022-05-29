# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 22:38:24 2013

@author: Winand
"""

#resource compilation
#pyrcc4 res/res.qrc -o res/res.py

import player_bass as bass
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QString, QUrl, pyqtSignal, Qt, QTimer, QDir#, QTranslator
from PyQt4.QtGui import QAbstractItemView, QPalette, QColor, QListView, QPainter, QImage, QGraphicsDropShadowEffect, QPixmap, QApplication
from playitem import PlayItem
from playlist import PlaylistSet, DoubleColumn, PlayItem as PlayItem2
from general import HourMinSec, overmind, bound
import math, sys
if sys.platform == 'win32':
    from windows import itaskbarlist3
    import windows.com as win32
    from windows.com import WINDOWPOS, WM_WINDOWPOSCHANGING, DRIVE_REMOVABLE, DRIVE_CDROM
    from windows.com import WM_DEVICECHANGE, DBT_DEVICEARRIVAL, DBT_DEVICEREMOVECOMPLETE, DEV_BROADCAST_HDR, DEV_BROADCAST_VOLUME, DBT_DEVTYP_VOLUME
from aufloatingwindow import AuFloatingWindow
from res import res #resources
from settings import MAIN

ogglink=0

class AuToolButton(QtGui.QToolButton):
    def paintEvent(self, e):
        if self.underMouse():
            p = QPainter(self)
            p.setBrush(QColor("#ffb06a"))
            p.setPen(QColor("#ffb06a"))
            p.drawRoundedRect(self.rect().adjusted(1,2,-2,-3),1,1)
        super(type(self), self).paintEvent(e)

class AuTreeView(QtGui.QTreeView):
    resize = pyqtSignal(int, int)
    def resizeEvent(self, e):
        self.resize.emit(e.size().width(), e.size().height())
        
class AuSpectrumBox(QtGui.QWidget):
    player = None
    
    def __init__(self, parent=None):
        overmind(self).__init__(parent)
        self.backColor = self.palette().color(self.backgroundRole())
        self.__init_img()
        self.mode = 0
        
    def paintEvent(self, e):
        QPainter(self).drawImage(0,0,self.img)
        
    def setPlayer(self, player=None):
        self.player = player
        self.img = QImage(self.width(), self.height(), QImage.Format_RGB32)
    
    def __init_img(self):
        w, h = self.width(), self.height()
        img = QImage(w, h, QImage.Format_RGB32)
        img.fill(self.backColor)
        self.img = img
        return img, w, h
        
    def render(self):
        img, w, h = self.__init_img()
        p = QPainter(img)
        
        if self.mode == 0:
            fft = self.player.getData()
            b0, bands = 0, w // 5
            for x in range(bands):
                summ = 0
                b1 = 2 ** (x * 10 / (bands-1))
                if b1 > 1023: b1 = 1023
                if b1 <= b0: b1 = b0 + 1 #make sure it uses at least 1 FFT bin
                sc = 10 + b1 - b0
                while True:
                    summ += fft[1+b0]
                    b0 += 1
                    if b0 == b1: break
                y = math.sqrt(summ / math.log(sc, 10)) * 1.7 * h - 4 #scale it
                if y > h: y = h # cap it
                p.setPen(Qt.NoPen)
                p.setBrush(Qt.black)
                p.drawRect(x*5, h-y, 4, y)
        elif self.mode == 1:
            buf, chans = self.player.getFloatData(w)
            for C in range(chans):
                #left=green, right=red (could add more colours to palette for more chans)
                v_buf = [int((1 - buf[x * chans + C]) * h / 2) for x in xrange(w)]
                col = 0xf00000 if C&1 else 0x00f000
                for x in xrange(w):
                    v = v_buf[x] #invert and scale to fit display
                    if v < 0:
                        v = 0
                    elif v >= h:
                        v = h - 1
                    if x == 0:
                        y = v
                        for i in range(h-v):
                            img.setPixel(0, v+i, col)
                    elif x == w-1:
                        for i in range(h-v):
                            img.setPixel(x, v+i, col)
                    else:
                        while True: #draw line from previous sample...
                            if y < v:
                                y += 1
                            elif y > v:
                                y -= 1
                            img.setPixel(x, y, col)
                            if y == v: break
        self.update()
        
    def mousePressEvent(self, e):
        self.mode += 1
        if self.mode > 1: self.mode = 0
            
class AuFileDialog(QtGui.QFileDialog):
    def __init__(self, *args, **kwargs):
        print args, kwargs
        overmind(self).__init__(*args, **kwargs)
        QtGui.QPushButton(self)

class AuMainWindow(QtGui.QMainWindow):
    def __init__(self):
        overmind(self).__init__()
        from PyQt4.QtGui import QWidget
        print type(self) == QWidget
        uic.loadUi("aumainwindow.ui", self)
        self.popupFolders.menuAction().setVisible(False) #hide popups
        self.main_menu.menuAction().setVisible(False)
                
        self.orig_wnd_title = self.windowTitle()
        self.show()
        self.btnFileOpen.clicked.connect(self.btnFileOpen_clicked)
#        self.mnuExit.triggered.connect(self.closeEvent)
        self.btnPrevOggLink.clicked.connect(self.btnPrevOggLink_clicked)
        self.btnNextOggLink.clicked.connect(self.btnNextOggLink_clicked)
        self.btnPrev.clicked.connect(self.btnPrev_clicked)
        self.btnPlay.clicked.connect(self.btnPlay_clicked)
        self.btnNext.clicked.connect(self.btnNext_clicked)
        
        lists = PlaylistSet().load(r'lst.zip')
        self.tabs.setTabList(lists, "Title")
        self.tabs.setShape(QtGui.QTabBar.RoundedSouth)
        #self.tabs.setUsesScrollButtons(False)
        self.tabs.currentChanged.connect(self.tabChanged)
        #self.tabs.setDrawBase(False)
        
        self.plv.setModel(self.tabs.tabData(0))
        self.plv.setSortingEnabled(True)
        self.plv.activated.connect(self.trackActivated)
        self.plv.resize.connect(self.playlist_resize)
        self.delegate = DoubleColumn()
        self.plv.setItemDelegateForColumn(3, self.delegate)
        self.plv.header().setResizeMode(QtGui.QHeaderView.Fixed)
        self.plv.setRootIsDecorated(False)
        self.plv.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.plv.setAlternatingRowColors(True)
        pal = self.plv.palette()
        pal.setColor(QPalette.AlternateBase, pal.color(QPalette.AlternateBase).lighter(102))
        self.plv.setPalette(pal)
##        self.plv.setDragEnabled(True)
##        self.plv.setAcceptDrops(True)
##        self.plv.setDropIndicatorShown(True)
#        self.plv.setDragDropMode(QListView.DragDrop)
#        self.plv.setDropIndicatorShown(False)
#        #self.plv.setDragDropOverwriteMode(False)
        self.plv.minimode = False
        self.plv.setUniformRowHeights(True) #no lags on 1st time scrolling
        self.plv.setAllColumnsShowFocus(True)
        self.plv.setAttribute(Qt.WA_MacShowFocusRect, 0)
        
        self.txtSearch.textEdited.connect(self.searchbox_change)
        self.filter_postpone_timer = QTimer()
        self.filter_postpone_timer.setSingleShot(True)
        self.filter_postpone_timer.timeout.connect(self.filter_postponed)
        
        self.volumeBar.slim_factor = 7
        self.volumeBar.userChanged.connect(self.vol_user_control)
        vol = bass.volume()
        self.volumeBar.addTextItem("vol%", "%.0f%%" % (vol*100))
        self.volumeBar.value = vol
        
        self.progress.changed.connect(self.progress_change)
        self.progress.userChanged.connect(self.progress_user_change)
        self.progress.mouseMove.connect(self.progress_mouse_move)
        self.progress.addTextItem("elapsed", "0%", Qt.AlignLeft+Qt.AlignVCenter)
        self.progress.addTextItem("remains", "100%", Qt.AlignRight+Qt.AlignVCenter)
        self.progressTip = None
        self.img_pos = QPixmap(":/img_pos")
        self.progressTimer = 0
        
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(0)
        effect.setColor(Qt.white)
        effect.setOffset(1, 1)
        self.lblAudica.setGraphicsEffect(effect)
        
        self.btnOpen.clicked.connect(self.btnOpen_clicked)
        self.volumes = {}
        self.manageVolumes([str(i.absolutePath())[:1] for i in QDir.drives()])
        
        self.btnVolumes.setMenu(self.popupFolders)
        self.btnMainMenu.setMenu(self.main_menu)
        
#    def __del__(self):
#        ps = PlaylistSet()
#        ps.save(r'lst1.txt', self.lists)
        
    def btnOpen_clicked(self):
#        AuFileDialog.getOpenFileName(None, "open", "", \
#                                    ";;".join((bass.Filter,"All files (*.*)")))
#        dialog = AuFileDialog()
#        dialog.exec_()
#        filename = unicode()
        #filename= u'http://94.25.53.133/ultra-192.m3u'
        #filename=u'http://translate.google.com/translate_tts?tl=en&q=Who%20am%20i'
        filename = unicode(QtGui.QFileDialog().getOpenFileName(None, "open", "", \
                                    ";;".join((bass.Filter,"All files (*.*)"))))
        print filename.encode('utf-8')
        if filename:
            pi = PlayItem2()
            pi.path = filename
            pi.remote = filename.startswith("http://")
            self.plv.model().items.append(pi)
            self.plv.model().layoutChanged.emit()
        
    def searchbox_change(self, text):
        if not self.filter_postpone_timer.isActive():
            self.filter_postpone_timer.start(50)
        
    def filter_postponed(self):
        self.plv.model().setFilter(str(self.txtSearch.text()))

    def timer_update_spectrum(self):
        self.spectrumBox.render()
        #WDM colorization
        if False:
            level = self.player.getLevel()
            level = ((level >> 16) + (level & 0xffff)) / 2 // 128
            if level == 256: level = 255 #Cap it.
            if level - self.prev > 50: level = self.prev + 50
            elif self.prev - level > 50: level = self.prev
            if level < 128: p = (level*2<<8)+   (128+level)         <<8
            else:           p = (0xff00)    +   (256-(level-127)*2) <<8
            win32.DwmSetColorizationParametersEx(p)
            self.prev = level
    
    def vol_user_control(self, v):
        "User changed volume"
        self.volumeBar.setTextItem("vol%", "%.0f%%" % (v*100))
        bass.setVolume(v)
        
    def progress_change(self, v):
        el = HourMinSec(self.player.getPosition()) + ' / ' + \
            "%.2f%%" % (self.player.getPosition() / self.player.getLength()*100)
        re = HourMinSec(self.player.getLength() - self.player.getPosition()) + ' / ' + \
            "%.2f%%" % ((1-self.player.getPosition() / self.player.getLength())*100)
        self.progress.setTextItem("elapsed", el)
        self.progress.setTextItem("remains", re)
        
    def progress_user_change(self, v):
        self.player.setPosition(self.player.getLength()*v)
        
#    def mapRcToGlobal(self, w):
#        rc = w.geometry()
#        rc.moveTopLeft(w.mapToGlobal(rc.topLeft()))
        
    def progress_mouse_move(self, action, gpos):
        gprogr_tl = self.mapToGlobal(self.progress.geometry().topLeft())
        gpos.setX(bound(gprogr_tl.x(), gpos.x(), \
                    self.mapToGlobal(self.progress.geometry().topRight()).x())
                  -self.img_pos.width()/2)         
        gpos.setY(gprogr_tl.y()-self.img_pos.height()/2)
        if action == 0:
            self.progressTip = AuFloatingWindow(self.progress)
            self.progressTip.setGeometry(self.img_pos.rect())
            self.progressTip.show()
            self.progressTip.move(gpos)
            self.progressTip.paint.connect(self.progress_tip_paint)
        elif action == 1 and self.progressTip:
            self.progressTip.move(gpos)
            self.progressTip.update()
        elif self.progressTip:
            self.progressTip.deleteLater()
            self.progressTip = None
            
    def progress_tip_paint(self, p):
        p.drawPixmap(0,0,self.img_pos)
        p.setPen(Qt.white)
        #p.setFont(QFont("Arial", 30));
        rc = self.progressTip.rect()
        rc.setBottom(14)
        txt = HourMinSec(self.player.getLength()*self.progress.valueFromCursor())
        p.drawText(rc, Qt.AlignCenter, txt);
    
    def playlist_resize(self, w, h):
        minimode = w <= 316
        if minimode != self.plv.minimode:
            self.plv.minimode = minimode
            self.plv.setHeaderHidden(minimode)
            self.plv.setColumnHidden(2, minimode)
            self.plv.setColumnHidden(3, minimode)
            self.spectrumBox.setVisible(not minimode)
        header = self.plv.header()
        if not minimode:
            w3 = 85.0
            w02 = w - w3
            header.resizeSection(0, w02/7*3)
            header.resizeSection(1, w02/7*2)
            header.resizeSection(2, w02/7*2)
            header.resizeSection(3, w3)
        else:
            header.resizeSection(0, w/5*3)
            header.resizeSection(1, w/5*2)
        
    def tabChanged(self, index):
        self.plv.setModel(self.tabs.tabData(index))
        
    def trackActivated(self, index):
        self.player = bass.Player()
        item = self.plv.model().items[index.row()]
        self.player.streamCreate(item, callback=self.opened)
    
    def btnNextOggLink_clicked(self):
        for i in range(self.plv.model().rowCount()):
            player = bass.Player()
            item = self.plv.model().items[i]
            player.streamCreate(item, callback=self.opened2)
#        global ogglink
#        self.player.goToOggLink(ogglink)
#        ogglink += 1
            
    def opened2(self, player, success):
        if success:
            player.getId3AlbumArt()
            if player.unsync:
                print "UNSYNC FOUND", player.p.path
        
    def btnPrevOggLink_clicked(self):
        PlaylistSet().save(r'lst.zip', self.tabs.tabsData())
        #self.player.getpos()
        
    def btnFileOpen_clicked(self):
        filename = unicode(QtGui.QFileDialog.getOpenFileName(None, "open", "", \
                                    ";;".join((bass.Filter,"All files (*.*)"))))
        #filename= u'http://94.25.53.133/ultra-192.m3u'
        #filename=u'http://translate.google.com/translate_tts?tl=en&q=Who%20am%20i'
        print filename.encode('utf-8')
        if filename:
            self.player = bass.Player()
            self.player.streamCreate(PlayItem(filename), \
                is_remote=filename.startswith("http://"), callback=self.opened)
        
#    def closeEvent(self, event):
#        self.saveModelToFile("model.txt")
#        QtCore.QCoreApplication.instance().quit()

    def opened(self, player, success):
        if not success:
            self.setWindowTitle(QString.fromUtf8("file cannot be opened Привет"))
            return
        player.streamPlay() #Start opened stream
        self.setWindowTitle(bass.getFormatDesc(player.getInfo()))
        self.lbltags.setText(QString.fromUtf8("\n".join([i for i in player.getStreamTags()])))
        self.killTimer(self.progressTimer) #FIXME: move to stream close
        self.progressTimer = self.startTimer(500)
        self.progress.setEnabled(True)
        
        self.timer_spectrum_upd = QTimer()
        self.timer_spectrum_upd.timeout.connect(self.timer_update_spectrum)
        self.timer_spectrum_upd.start(40)
        self.prev = 0
        
        self.spectrumBox.setPlayer(self.player)
        
        art = self.player.getId3AlbumArt()
        if art:
            self.lblAudica.setPixmap(art)
        
    def timerEvent(self, e):
        self.progress.value = self.player.getPosition() / self.player.getLength()

    #    links = player.getOggLinkNumber()
    #    print "1/"+str(links), player.getStreamTags()
    #    while(True):
    #        x = raw_input()
    #        if x=="":
    #            QtGui.QApplication.quit()
    #            break
    #        elif x.isdigit():
    #            link = int(x)-1
    #            if 0 <= link < links:
    #                player.goToOggLink(link)
    #                print x+"/"+str(links), player.getStreamTags()
    #            else: print "Link not found"
    #        else: print "Enter link number"

    def wheelEvent(self, e):
        self.volumeBar.wheelEvent(e) #pass to volume bar
        
    def btnPrev_clicked(self):
        print "btnprev", win32.getVolumeInformation('g')
        
    def btnPlay_clicked(self):
        print "btnplay"
        
    def btnNext_clicked(self):
        print "btnnext"
        
    def taskbar_buttonPress(self, button):
        "Win32 taskbar buttons"
        (self.btnPrev, self.btnPlay, self.btnNext) \
                        [button].clicked.emit(False)
                        
                        
    def manageVolumes(self, vols, rem=False):
        for i in vols:
            islash = i+':\\'
            if not rem:
                drivet = win32.GetDriveType(islash)
                if drivet in (DRIVE_REMOVABLE, DRIVE_CDROM):
                    if not win32.isFloppyDrive(i): #Not a floppy
                        descr, vserial = win32.getVolumeInformation(i)
                        descr = descr or ('CD-ROM' if drivet==DRIVE_CDROM else 'Removable')
                        if vserial > 0 and islash not in self.volumes:
                            self.volumes[islash] = descr
                            self.popupFolders.addAction(islash+'\t'+descr \
                                                        ).setProperty(islash, True)
                            print 'Volume detected', i
            elif islash in self.volumes:
                self.popupFolders.removeAction( \
                            next(act for act in self.popupFolders.actions() \
                                if act.property(islash).toBool()))
                del self.volumes[islash]
                print 'Volume disconnected', i
        
    def winEvent(self, message):
        if message.message == WM_WINDOWPOSCHANGING:
            stickAt = MAIN.STICKY_WINDOW_PX
            pos = WINDOWPOS.from_address(message.lParam)
            mon = QApplication.desktop().availableGeometry(self)
            if abs(pos.x - mon.left()) <= stickAt:
                pos.x = mon.left()
            elif abs(pos.x + pos.cx - mon.right()) <= stickAt:
                pos.x = mon.right() - pos.cx
            if abs(pos.y - mon.top()) <= stickAt:
                pos.y = mon.top()
            elif abs(pos.y + pos.cy - mon.bottom()) <= stickAt:
                pos.y = mon.bottom() - pos.cy
        elif message.message == WM_DEVICECHANGE:
            if message.wParam in (DBT_DEVICEARRIVAL, DBT_DEVICEREMOVECOMPLETE):
                devvol = DEV_BROADCAST_HDR.from_address(message.lParam)
                if devvol.dbch_devicetype == DBT_DEVTYP_VOLUME:
                    mask = DEV_BROADCAST_VOLUME.from_address(message.lParam).dbcv_unitmask
                    letters = [chr(65+sh) for sh in range(26) if mask>>sh&1]
                    self.manageVolumes(letters, rem = message.wParam==DBT_DEVICEREMOVECOMPLETE)
        return False, 0

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
#    translator=QtCore.QTranslator()
#    translator.load("tr-ru.qm")
#    app.installTranslator(translator)
    bass.init()
    mainwnd = AuMainWindow()
    if sys.platform == 'win32':
        taskbar = itaskbarlist3.ITaskBarList3(mainwnd)
        if taskbar.isAccessible():
            icons = ((QPixmap(":/windows/taskbar_prev"), u"Previous"), \
                     (QPixmap(":/windows/taskbar_pause"), u"Play"), \
                     (QPixmap(":/windows/taskbar_next"), u"Next"))
            taskbar.ThumbBarAddButtons(icons)
            taskbar.buttonPress.connect(mainwnd.taskbar_buttonPress)
    ret = app.exec_()
    if sys.platform == 'win32':
        del taskbar #otherwise crashes on taskbar.__del__'s Release
    bass.destroy()
    sys.exit(ret)