# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 22:38:24 2013

@author: Winand
"""

#resource compilation
#pyrcc4 res/res.qrc -o res/res.py

import player_bass as bass
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QString, QUrl, pyqtSignal, Qt, QTimer, QDir, QRect, QSize, QPoint, QEvent, QRegExp, QString#, QTranslator
from PyQt4.QtGui import QAbstractItemView, QPalette, QColor, QPainter, QImage, \
    QGraphicsDropShadowEffect, QPixmap, QApplication, QRubberBand, QFont, QIcon, QMenu, QCursor, QDesktopServices
from playitem import PlayItem
import playlist
from playlist import PlaylistSet, DoubleColumn, PlayItem as PlayItem2
from general import HourMinSec, overmind, bound, divide_size, isWin32, s, s2
import math, sys
if isWin32():
    from windows import itaskbarlist3
    import windows.com as win32
    from windows.com import WINDOWPOS, WM_WINDOWPOSCHANGING, DRIVE_REMOVABLE, DRIVE_CDROM
    from windows.com import WM_DEVICECHANGE, DBT_DEVICEARRIVAL, DBT_DEVICEREMOVECOMPLETE, DEV_BROADCAST_HDR, DEV_BROADCAST_VOLUME, DBT_DEVTYP_VOLUME
from aufloatingwindow import AuFloatingWindow
from res import res #resources
from settings import MAIN as P, save_settings

song_info_template = u"""<html><head><style type="text/css">a{{color:black; text-decoration: none;}} td{{vertical-align: middle; padding-right:3px;}}</style></head><body>
<table cellspacing=0 border=1><tr><td><img src=":/tags/icon/song"/></td><td><span style="font-size:{song_size}pt">{song}</span></td></tr>
<tr><td><a href="web:0://{artist_search}"><img src=":/tags/icon/artist"/></a></td><td><a href="filter://{artist_search}">{artist}</a></td></tr>
<tr><td><a href="web:1://{album_search}"><img src=":/tags/icon/album"/></a></td><td><a href="filter://{album_search}">{album}</a></td></tr>
<tr><td><img src=":/tags/icon/info"/></td><td>{info}</td></tr></table>
</body></html>"""
song_label_size = P.SONG_LABEL_SIZE[0]

ogglink=0

class AuToolButton(QtGui.QToolButton):
    def paintEvent(self, e):
        if self.underMouse():
            p = QPainter(self)
            p.setBrush(QColor("#ffb06a"))
            p.setPen(QColor("#ffb06a"))
            p.drawRoundedRect(self.rect().adjusted(1,2,-2,-3),1,1)
        overmind(self).paintEvent(e)

class AuPlaylistView(QtGui.QTableView): #QTreeView
    resized = pyqtSignal(int, int)
    
    def __init__(self, *args, **kwargs):
        overmind(self).__init__(*args, **kwargs)
#!        self.header().setResizeMode(QtGui.QHeaderView.Fixed)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
#        self.verticalHeader().setMovable(True)
#!        self.setSelectionBehavior(QAbstractItemView.SelectRows)
#!        self.setRootIsDecorated(False)
#!        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
##        self.plv.setDragEnabled(True)
##        self.plv.setAcceptDrops(True)
##        self.plv.setDropIndicatorShown(True)
#        self.plv.setDragDropMode(QListView.DragDrop)
#        self.plv.setDropIndicatorShown(False)
#        #self.plv.setDragDropOverwriteMode(False)
#        self.verticalHeader().setHidden(True)
#!        self.plv.setUniformRowHeights(True) #no lags on 1st time scrolling
#!        self.plv.setAllColumnsShowFocus(True)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        
    def resizeEvent(self, e):
        overmind(self).resizeEvent(e)
        self.resized.emit(e.size().width(), e.size().height())
        
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
        uic.loadUi("aumainwindow.ui", self)
        for i in self.menuBar.findChildren(QMenu, QRegExp("popup.+")):
            i.menuAction().setVisible(False) #hide popups
                
        self.orig_wnd_title = self.windowTitle()
        self.show()
        self.btnFileOpen.clicked.connect(self.btnFileOpen_clicked)
#        self.mnuExit.triggered.connect(self.closeEvent)
        self.btnPrevOggLink.clicked.connect(self.btnPrevOggLink_clicked)
        self.btnNextOggLink.clicked.connect(self.btnNextOggLink_clicked)
        self.btnPrev.clicked.connect(self.btnPrev_clicked)
        self.btnPlay.clicked.connect(self.btnPlay_clicked)
        self.btnNext.clicked.connect(self.btnNext_clicked)
        self.lbltags.linkActivated.connect(self.headertext_clicked)
        
        lists = PlaylistSet().load(r'lst.zip')
        self.tabs.changed.connect(self.updatePlaylistMenu)
        self.tabs.setTabList(lists, "Title")
        self.tabs.setShape(QtGui.QTabBar.RoundedSouth)
        #self.tabs.setUsesScrollButtons(False)
        self.tabs.setCurrentIndex(P.CURRENT_TAB)
        self.tabChanged(P.CURRENT_TAB)
        self.tabs.currentChanged.connect(self.tabChanged)
        #self.tabs.setDrawBase(False)

        self.plv.minimode = None
        self.plv.setItemDelegateForColumn(3, DoubleColumn())
        self.playlist_resize(self.plv.width()-2, self.plv.height()-2) #"-2" - border?
        self.plv.resized.connect(self.playlist_resize)
        self.plv.activated.connect(self.trackActivated)
        
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
        
        self.popupPlaylists.triggered.connect(self.showPlaylist)
        self.btnVolumes.setMenu(self.popupFolders)
        self.btnMainMenu.setMenu(self.popup_main_menu)
        self.btnPlaylists.setMenu(self.popupPlaylists)
        self.popup_web_info.triggered.connect(self.web_info_clicked)
        for i in P.WEB_INFO.keys():
            self.popup_web_info.addAction(i)
        self.lbltags.setText(song_info_template.format( \
            song="Дожили".decode("utf-8"), song_size=song_label_size, \
            artist="AC/DC", artist_search="Машина времени".decode("utf-8"), \
            album="asdfd", album_search="asdfgh", \
            info="#33, raggae"))
        self.lblAudica.setVisible(False)
        self.lblAlbumArt.setVisible(False)
        
#    def __del__(self):
#        ps = PlaylistSet()
#        ps.save(r'lst1.txt', self.lists)
        
    def web_info_clicked(self, act):
        url = P.WEB_INFO[unicode(act.text())]
        if type(url) is tuple:
            url = url[self.popup_web_info.property("type").toInt()[0]]
        url = url.replace("#QRY#", \
                            unicode(self.popup_web_info.property("ref").toString()))
        QDesktopServices.openUrl(QUrl(url))
        
    def headertext_clicked(self, link):
        protocol, ref = link.split("://")
        if protocol == "filter":
            self.txtSearch.setText(ref)
            self.filter_postponed()
        elif str(protocol).startswith("web:"):
            self.popup_web_info.setProperty("ref", ref)
            self.popup_web_info.setProperty("type", int(protocol[-1]))
            self.popup_web_info.exec_(QCursor.pos())
        
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
            pi.remote = filename.startswith("http://") #FIXME: http only?
            self.plv.model().items.append(pi)
            self.plv.model().layoutChanged.emit()
        
    def searchbox_change(self, text):
        if not self.filter_postpone_timer.isActive():
            self.filter_postpone_timer.start(50)
        
    def filter_postponed(self):
        self.plv.model().setFilter(unicode(self.txtSearch.text()))

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
        minimode = (w <= P.MINIUI_WIN_WIDTH+P.PL_BAR_W if self.plv.minimode \
                                            else w <= P.MINIUI_WIN_WIDTH)
#!        header = self.plv.header()
        header = self.plv.horizontalHeader()
        if minimode != self.plv.minimode:
            self.plv.minimode = minimode
#!            self.plv.setHeaderHidden(minimode)
            header.setHidden(minimode)
            self.plv.setColumnHidden(2, minimode)
            self.plv.setColumnHidden(3, minimode)
            self.spectrumBox.setVisible(not minimode)
            self.tabs.setVisible(not minimode)
#            self.btnPlaylists.setVisible(minimode)
            self.lblPlaylistInfo.setVisible(not minimode)
            f = self.lblAudica.font()
            f.setPointSize(P.LABEL_SIZE[minimode])
            self.lblAudica.setFont(f)
            global song_label_size
            song_label_size = P.SONG_LABEL_SIZE[minimode]
        col_sizes = divide_size(w, *P.COLUMN_SIZES[minimode])
        for i in range(len(col_sizes)):
            header.resizeSection(i, col_sizes[i])
        
    def tabChanged(self, index):
        self.playlist = self.tabs.tabData(index)
        self.plv.setModel(self.playlist)
        P.CURRENT_TAB = index
        
    def trackActivated(self, index):
        self.playlist.playing = index.row()
        self.plv.repaint()
        self.player = bass.Player()
        item = self.playlist.modelIdxToItem(index)
        self.player.streamCreate(item, callback=self.opened)
        print song_label_size
        self.lbltags.setText(song_info_template.format( \
            song=item.Song, song_size=song_label_size, \
            artist=item.Artist, artist_search=item.Artist, \
            album=item.Album, album_search=item.Album, \
            info=s2(s("#",item.Track), ", ", "$stub$")))
    
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
        
    def closeEvent(self, event):
        save_settings()
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
            self.lblAlbumArt.setPixmap(art)
            self.lblAlbumArt.setVisible(True)
            
        print self.player.getStreamTags()
        
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
                        
    def updatePlaylistMenu(self):
        self.popupPlaylists.clear()
        for i in range(self.tabs.count()):
            act = self.popupPlaylists.addAction(self.tabs.tabText(i))
            if self.tabs.currentIndex() == i:
                b = QFont()
                b.setBold(True)
                act.setFont(b)
            
    def showPlaylist(self, act):
        self.tabs.setCurrentIndex(self.popupPlaylists.actions().index(act))
                        
    def manageVolumes(self, vols, rem=False):
        #FIXME: other platforms
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
            stickAt = P.STICKY_WINDOW_PX
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
        
#    def eventFilter(self, obj, e):
#        print e
#        if e.type() == QEvent.MouseButtonPress:
#            print 1
#            self.rb_orig = e.pos()
#            if not self.rb:
#                self.rb = QRubberBand(QRubberBand.Rectangle, self.plv)
#            self.rb.setGeometry(QRect(self.rb_orig, QSize()))
#            self.rb.show()
#            return True
#        elif e.type() == QEvent.MouseMove:
#            print 2
#            if self.rb:
#                self.rb.setGeometry(QRect(self.rb_orig, e.pos()).normalized())
#                return True
#        elif e.type() == QEvent.MouseButtonRelease:
#            print 3
#            self.rb.hide()
#            return True
#        return overmind(self).eventFilter(obj, e) 
        
if __name__ == '__main__':
    if isWin32():
        win32.SetCurrentProcessExplicitAppUserModelID('winand.audica.osap.9') #don't group
    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QIcon().loadIco(":/main_icon"))
#    translator=QtCore.QTranslator()
#    translator.load("tr-ru.qm")
#    app.installTranslator(translator)
    bass.init()
    mainwnd = AuMainWindow()
    if isWin32():
        taskbar = itaskbarlist3.ITaskBarList3(mainwnd)
        if taskbar.isAccessible():
            icons = ((QPixmap(":/windows/taskbar_prev"), u"Previous"), \
                     (QPixmap(":/windows/taskbar_pause"), u"Play"), \
                     (QPixmap(":/windows/taskbar_next"), u"Next"))
            taskbar.ThumbBarAddButtons(icons)
            taskbar.buttonPress.connect(mainwnd.taskbar_buttonPress)
    ret = app.exec_()
    if isWin32():
        del taskbar #otherwise crashes on taskbar.__del__'s Release
    bass.destroy()
    sys.exit(ret)