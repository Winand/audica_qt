# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 23:58:38 2013

@author: Winand

'Class implementing
'Last.fm Submissions Protocol v1.2.1
'Written according to
'http://www.lastfm.ru/api/submissions
'Winand, 2009 (started 09-09-14)
"""

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QApplication
from general import ddict

import calendar, datetime, hashlib, string, re, urllib
REG_EXP_URL = r"((http|ftp)://)?(([0-9]{1,3}\.){3}[0-9]{1,3}|(www\.)?[^ /\\]+\.[a-z]{2,})(:[0-9]{1,5})?(/[^ ]*)?"

DEFAULT_HSURL = "http://post.audioscrobbler.com"
CLIENTS = (('tst','1.0'), ('ass','1.5.4.24567'), ('cub','0.0.11'))
DEFAULT_CLIENT, DEFAULT_CLIENTVER = CLIENTS[1] #I'm Last.fm Scrobbler
PROTOVER = "1.2.1"
statuses = ddict(MUSTHANDSHAKE=0, HANDSHAKING=1, WILLHANDSHAKE=2, CONNECTED=3, CANNOTCONNECT=4, DISABLED=5)

def UNIXTime(local):
    nowf = datetime.datetime.now if local else datetime.datetime.utcnow
    return calendar.timegm(nowf().utctimetuple())
    
def isMD5(text):
    return all(x in string.hexdigits for x in text) and len(text)==32

class LastFMScrobbler():
    Id = ddict(ok=False) #user, md5pass
    serv = ddict(ok=False) #client, clientV, hsURL, hsUTC
    status = statuses.CANNOTCONNECT
    req_hs = None
    netw = QNetworkAccessManager()
    
    def __init__(self, user, passw, secret=True, client=DEFAULT_CLIENT, \
                clientV=DEFAULT_CLIENTVER, hsURL=DEFAULT_HSURL, hsUTC=False):
        self.setUserCreds(user, passw, secret)
        self.setClientCreds(client, clientV, hsURL, hsUTC)
        self.disable()
            
    def setUserCreds(self, user, passw, secret):
        if not secret and passw:
            passw = hashlib.md5(passw).hexdigest() 
        if user and isMD5(passw):
            self.Id.user = user
            self.Id.md5pass = passw
            self.Id.ok = True
            
    def setClientCreds(self, client, clientV, hsURL, hsUTC):
        if client and clientV and re.match(REG_EXP_URL, hsURL):
            self.serv.client = client
            self.serv.clientV = clientV
            self.serv.hsURL = hsURL
            self.serv.hsUTC = hsUTC
            self.serv.ok = True
    
    def credsOk(self):
        return self.Id.ok and self.serv.ok
        
    def setEnabled(self, enabled):
        self.status = statuses.MUSTHANDSHAKE if enabled else statuses.DISABLED
        if enabled:
            self.connect()
            
    def createHSQuery(self):
        LAST_FM_HS_REQUEST = "/?hs=true&p={proto}&c={clientid}&v={clientver}&u={user}&t={timestamp}&a={auth}"
        timestamp = str(UNIXTime(local=self.serv.hsUTC))
        auth = hashlib.md5(self.Id.md5pass + timestamp).hexdigest()
        return LAST_FM_HS_REQUEST.format(clientid=self.serv.client, \
                                        clientver=self.serv.clientV, \
                                        user=self.Id.user, auth=auth, \
                                        timestamp=timestamp, proto=PROTOVER)
    
    def pe(self, text):
        "convert to UTF-8 and percent-encode"
        return urllib.quote(text.encode('utf-8'), safe='')
        
    def connect(self):
        if self.status == statuses.DISABLED or self.status == statuses.CONNECTED:
            return False
        if not self.credsOk(): #all ok
            return False
        if self.req_hs and self.req_hs.isRunning():
            self.req_hs.abort() #abort previous handshake if any
        hs_get_url = QUrl(self.serv.hsURL+self.createHSQuery())
        self.req_hs = self.netw.get(QNetworkRequest(hs_get_url))
        self.req_hs.finished.connect(self.__handshakeFinished)
        return True

    def __handshakeFinished(self):
        print self.req_hs.readAll()

app = QApplication([])
key='9ce837d3aae305c0****************'
lFM = LastFMScrobbler("Winand","a87ff679a2f3e71d****************")
lFM.setEnabled(True)
ret = app.exec_()
