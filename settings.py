# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 20:42:12 2014

@author: Winand
"""

from general import ddictEx
import pickle
brainz_s = "http://musicbrainz.org/search?query=#QRY#&type="

TABBAR = ddictEx( \
    ACTIVE_LINE = "#ff8000", #color of line drawn over active tab
)
    
MAIN = ddictEx( \
    STICKY_WINDOW_PX = 10, #px, stick to screen edge at this distance
    PLAYLIST_ROW_HEIGHT = 17, #px
    MINIUI_WIN_WIDTH = 316, #px, switch to mini-ui at this window width
    PL_BAR_W = 20,
    #                auto|25%|25%|85px,  60%|auto - standard ui, mini ui
    COLUMN_SIZES = ((0, 0.25, 0.25, 85),(0.6, 0)),
    LABEL_SIZE = (57, 37), #pt, AUDICA label size
    SONG_LABEL_SIZE = (16, 12),
    CURRENT_TAB = 0,
    WEB_INFO = {"Last.fm": "http://www.last.fm/search?q=#QRY#",
                "MusicBrainz": (brainz_s+"artist", brainz_s+"release")}
)

PLAYER_BASS = ddictEx( \
    COVER_FILES = ("cover", "folder", "*AlbumArt*"), #add front too? Aerosmith_-_Just_Push_Play-front.jpg
    COVER_EXTS = ("jpg","jpeg","png","gif","bmp")
)

GROUPS = ("TABBAR", "MAIN", "PLAYER_BASS")

def modify(new, old):
    "add and delete settings according to /old/ settings"
    plus, minus = tuple(set(old.keys())-set(new.keys())), \
                    tuple(set(new.keys())-set(old.keys()))
    for i in plus:
        new[i] = old[i]
        print("ADD SETTING:", i)
    for i in minus:
        del new[i]
        print("DEL SETTING:", i)

def save_settings():
    with open("options.ini", 'wb') as f:
        pickle.dump(tuple(globals()[i] for i in GROUPS), \
                    f, pickle.HIGHEST_PROTOCOL)

try:
    with open("options.ini", 'rb') as f:
        LOADED = pickle.load(f)
#    assert len(LOADED) == len(GROUPS)
    for i, v in enumerate(LOADED):
        modify(v, globals()[GROUPS[i]])
        globals()[GROUPS[i]] = v
except (IOError, EOFError):
    print("Settings: first time load")
