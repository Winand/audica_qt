# -*- coding: utf-8 -*-
"""
Created on Fri Apr 05 18:34:20 2013

@author: Winand
"""

class PlayItem:
    handle = None
    stream = None
    remote = None
#    src = None
    
    def __init__(self, source = None):
        self.m_src = source
    
    @property
    def src(self):
        return self.m_src
    
    @src.setter
    def src(self, source):
        self.m_src = source
        #if source[:]