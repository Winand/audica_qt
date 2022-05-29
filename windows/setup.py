# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 17:41:26 2013

@author: Winand
"""

from cx_Freeze import setup, Executable

setup(
    name = "On Dijkstra's Algorithm",
    version = "3.1",
    description = "A Dijkstra's Algorithm help tool.",
    executables = [Executable("itaskbarlist3.py", base = "Win32GUI")],
    options = {"build_exe": {"includes":["sip", "atexit", "PyQt4.QtCore"], "include_files": ["../res"]}},)