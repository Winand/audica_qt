# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 19:54:07 2013

@author: Winand
"""

#from PyQt4.QtWebKit import QWebView, QWebSettings
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.QtCore import QUrl, Qt
from PyQt4.QtGui import QApplication, QDesktopServices, QDialog, QMessageBox
from PyQt4 import uic
import json, hashlib, urllib, cPickle, timeit
from res import res #resources
from general import ddict, NetworkInit


AUDICA_KEY = '9ce837d3aae305c0****************'
AUDICA_SECRET = 'b1c747efd076530b****************'
LASTFM_ROOT_URL = 'http://ws.audioscrobbler.com/2.0/'
LASTFM_ACCESS_URL = 'http://www.last.fm/api/auth/'
SETTINGS_FILE = "lastfm.txt"
sk = None #module-wide session key

#session = "{u'session': {u'subscriber': u'0', u'name': u'********', u'key': u'8243dfb4b1632f15****************'}}"
    
class lapicall():
    netw = None #class-wide QNetworkAccessManager
    def __init__(self, name, write=False):
        self.name = name
        self.write = write
        
    def __eq__(self, othername):
        return self.name == othername
        
    def __genReqUrl(self, **attrs):
        if self.write and not sk:
            print "lapicall: Write methods require sk!"
            return
        all_attrs = [(k, str(v).encode('utf-8')) for k, v in attrs.items()] + \
                            [('api_key', AUDICA_KEY), ('method', self.name)]
        if self.write: all_attrs.append(('sk', sk))
        sorted_attrs = sorted(all_attrs, key=lambda t: t[0])
        s = "".join([k+v for k, v in sorted_attrs]) + AUDICA_SECRET
        sign = hashlib.md5(s).hexdigest()
        url_attrs = all_attrs + [("api_sig", sign), ("format", "json")]
        return urllib.urlencode(url_attrs)
        
    def __call__(self, **attrs):
        prm = self.__genReqUrl(**attrs)
        if self.write:
            req = QNetworkRequest(QUrl(LASTFM_ROOT_URL))
            req.setHeader(QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
            reply = self.netw.post(req, prm)
        else:
            req = QNetworkRequest(QUrl(LASTFM_ROOT_URL+"?"+prm))
            reply = self.netw.get(req)
        reply.setProperty("method", self.name)
        

#Last.fm API
auth_api = ddict(getToken=lapicall('auth.getToken'), \
                getSession=lapicall('auth.getSession'))
track_api = ddict(updateNowPlaying=lapicall('track.updateNowPlaying', write=True), \
                scrobble=lapicall('track.scrobble', write=True))
lapi = ddict(auth=auth_api, track=track_api)
ERR_INVALIDSESSION = 9
#auth.getToken
ERR_GRANTTOKEN = 8 #There was an error granting the request token. Please try again later
#auth.getSession
ERR_TOKENINVALID = 4 #Invalid authentication token supplied
ERR_TOKENNOTAUTHED = 14 #This token has not been authorized
ERR_TOKENEXPIRED = 15 #This token has expired

def print_(text):
    print text

class LastFm2Scrobbler(object):
    def __init__(self):
        self.netw = QNetworkAccessManager()
        self.netw.finished.connect(self.network_callback)
        lapicall.netw = self.netw
#        lapicall.req1 = QNetworkRequest(QUrl(LASTFM_ROOT_URL))
#        lapicall.req1.setHeader(QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
        self.token = None
        
        self.w=QDialog()
        uic.loadUi("dlg_lastfm.ui", self.w)
        self.w.btnAuthToken.clicked.connect(self.btnAuthToken_clicked)
        self.w.btnAuthSession.clicked.connect(self.btnAuthSession_clicked)
        self.w.btnTest.clicked.connect(self.btnTest_clicked)
        self.w.chkScrobble.stateChanged.connect(self.chkScrobble_change)

        self.enabled = False
        try:
            global sk
            with file(SETTINGS_FILE, 'rb') as f:
                self.cache, sk, self.enable = cPickle.loads(f.read())
        except:
            self.cache, self.enable = [], False
        if sk:
            self.authGotoStep(4)
        
    def __del__(self):
        with file(SETTINGS_FILE, 'wb') as f:
            f.write(cPickle.dumps((self.cache, sk, self.enable), -1))
        
    def network_callback(self, reply):
        try:
            method = reply.property('method').toString()
            data = json.loads(str(reply.readAll()))
            self.reply_handler(method, data, data['error'] if 'error' in data else 0)
        except:
            print "network_callback error"
                
    def reply_handler(self, method, data, err=0):
        global sk
        #SUCCESS
        if not err:
            if method == lapi.auth.getToken:
                self.token = data['token']
                QDesktopServices.openUrl(QUrl('%s?api_key=%s&token=%s' % (LASTFM_ACCESS_URL, AUDICA_KEY, self.token)))
                self.authGotoStep(3)
            elif method == lapi.auth.getSession:
                self.token = None
                sk = data['session']['key']
                self.authGotoStep(4)
            elif method == lapi.track.updateNowPlaying:
                print "updateNowPlaying", data
            elif method == lapi.track.scrobble:
                self.cache = [] #items scrobbled successfully
        #ERRORS
        elif err == ERR_INVALIDSESSION:
            self.authGotoStep(1)
            sk = None #clear session key
            QMessageBox.warning(self.w, "Invalid session", "Your session key is invalid. Please, re-authenticate.")
        elif (method == lapi.auth.getToken and \
        err in (ERR_GRANTTOKEN,)) or \
        (method == lapi.auth.getSession and \
        err in (ERR_TOKENINVALID, ERR_TOKENEXPIRED)):
            self.token = None
            self.authGotoStep(1)
            QMessageBox.warning(self.w, "Authorization failed", "Authorization process failed (%s:%s)." % (method, err))
        elif method == lapi.auth.getSession and err == ERR_TOKENNOTAUTHED:
            #open access-granting webpage again
            QDesktopServices.openUrl(QUrl('%s?api_key=%s&token=%s' % (LASTFM_ACCESS_URL, AUDICA_KEY, self.token)))
        elif method == lapi.track.updateNowPlaying:
            print "E updateNowPlaying", data
        else:
            print "Unknown Last.fm reply error (%s:%s)." % (method, err)


    #TODO: make two caches
    def cache_item(self, artist, track, duration, timestamp):
        self.cache.append((artist, track, duration, timestamp))
        if len(self.cache) > 50:
            del self.cache[0]
        
    def updateNowPlaying(self, artist, song):
        lapi.track.updateNowPlaying(artist=artist, track=song)
        
    def scrobble(self, artist, track, duration, timestamp):
        if self.enable:
            attrs = {}
            self.cache_item(artist, track, duration, timestamp)
            if sk:
                for i, (a, t, ts) in enumerate(self.cache):
                    attrs['artist[%d]' % i] = a
                    attrs['track[%d]' % i] = t
                    attrs['timestamp[%d]' % i] = ts
                lapi.track.scrobble(**attrs)
        
    def isReady(self):
        return self.enable and sk
        
    def showPreferences(self):
        self.w.show()
        
    def __authSetControlsEnabled(self, token, session, scrobble_box):
        self.w.btnAuthToken.setEnabled(token)
        self.w.btnAuthSession.setEnabled(session)
        self.w.boxScrobble.setEnabled(scrobble_box)

    def authGotoStep(self, step):
        if step == 1:
            self.__authSetControlsEnabled(True, False, False)
        elif step == 3:
            self.__authSetControlsEnabled(False, True, False)
        elif step == 4: #finish
            self.__authSetControlsEnabled(True, False, True)
    
    def btnAuthToken_clicked(self):
        self.w.btnAuthToken.setEnabled(False)
        lapi.auth.getToken()
        
    def btnAuthSession_clicked(self):
        lapi.auth.getSession(token=self.token) if self.token else \
                    print_("Get authorization token first! (auth_getSession)")
    
    def btnTest_clicked(self):
        self.updateNowPlaying(u"Кино", u"Бла бла бла")
    
    def chkScrobble_change(self, state):
        self.enabled = state!=Qt.Unchecked

    @property
    def enable(self): return self.enabled
    @enable.setter
    def enable(self, enable):
        self.w.chkScrobble.setCheckState(Qt.Checked if enable else Qt.Unchecked)

if __name__ == '__main__':
    app = QApplication([])
    NetworkInit.init()
lastfm = LastFm2Scrobbler()
if __name__ == '__main__':
    lastfm.showPreferences()
    #lfm.enable = True
    ret = app.exec_()