#!/usr/env/python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import os.path
import tarfile
import logging
import datetime
import time
import traceback
import threading
import datetime
import sys
import logging.handlers
import threading


sys.path.append(os.path.dirname(__file__))

import tempUtils

try:
    scriptPath = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join('../../', 'wxmapwidget')))
    
    from PIL import Image
    
    import av
    import av.datasets
    
    import wx, wx.grid

    from com.kirayim.wxmapwidget.wxmapwidget import WxMapWidget, PosMarker, ScaleMarkLayer, DroneSymbol, SlippyLayer
    
    import cv2
    import numpy as np
except Exception as e:
    print(f'''
        Exception {e}, 
        {traceback.print_exc()}
        ----------------------------------------------------------
        Looks like some required packages were missing. To install:
        Ubuntu: sudo apt install python3-wxgtk4.0 python3-numpy python3-pil python3-opencv
        
        **NOTE**: You cannot install PyCV from Ubuntu repositories - use:
        Ubuntu 18.04: sudo -H pip3 install -Iv av==6.2.0
        Ubuntu 20.04: sudo -H pip3 install av
        
        Windows:
        pip install wxPython av pillow opencv-python
    ''')
    sys.exit(-2)

print("wxPython version", wx.__version__)

logger = logging.getLogger('tempwx')


# =============================================================================

def setupLogging():

    logdir = '/tmp/tempwx/logs'
    logger = logging.getLogger('tempwx')
    logger.setLevel(logging.DEBUG)
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    
    handler = logging.handlers.RotatingFileHandler(os.path.join(logdir, 'klvplayerQt5.log'),
                                                backupCount=30, maxBytes=1024 * 1024 * 10)
    
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s  %(filename)s(%(lineno)d)  %(funcName)s %(message)s')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    outhandler = logging.StreamHandler()
    outhandler.setLevel(logging.DEBUG)
    outhandler.setFormatter(formatter)
    logger.addHandler(outhandler)
    logger.debug("Starting up")

# =============================================================================

class StationsLayer(SlippyLayer):
    def __init__(self, stationsDf):
        self.stationsDf = stationsDf
    
    def do_draw(self, gpsmap, dc):
        size = gpsmap.GetSize()
        
        items = self.stationsDf[(gpsmap.S < self.stationsDf["LATITUDE"]) 
                                    & (self.stationsDf["LATITUDE"] < gpsmap.N)
                                    & (gpsmap.W < self.stationsDf["LONGITUDE"])
                                    & (self.stationsDf["LONGITUDE"] < gpsmap.E)
                                    ]
        
        for _, row in items.iterrows():
            lat, lon = row["LATITUDE"], row["LONGITUDE"]
            if gpsmap.isOnScreen(lat, lon):
                x, y = gpsmap.ll2xy(row["LATITUDE"], row["LONGITUDE"])
                dc.SetPen(wx.Pen(wx.BLACK, 2))
                dc.SetBrush(wx.Brush(wx.RED))
                dc.DrawCircle(int(x), int(y), 5)


# =============================================================================

class TempWidget(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Temp")

        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        
        downloadStations = fileMenu.Append(1, 'Download stations', 'Download stations file')
        
        quit = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        menuBar.Append(fileMenu, '&File')
        
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.Close, quit)
        self.Bind(wx.EVT_MENU, self.downloadSations, downloadStations)

        self.mapPanel = WxMapWidget(self)
        self.mapPanel.layer_add(PosMarker())
        self.mapPanel.layer_add(ScaleMarkLayer())
        
        self.statusbar = self.CreateStatusBar(1)

        self.stationsLayer = None

        
        threading.Thread(target=self.showStations).start()
        
        self.SetSize(0, 0, 1280 + 200, 960)
        self.Center()
        self.Show()


    # =============================================================================

    def showStations(self):
        if not tempUtils.hasStationsList():
            return
        
        if self.stationsLayer:
            self.mapPanel.layer_remove(self.stationsLayer)
            self.stationsLayer = None
        
        wx.CallAfter(self.statusbar.SetStatusText, 'Reading stations')
        self.stationsDf = tempUtils.readStations()
        self.stationsLayer = StationsLayer(self.stationsDf)
        self.mapPanel.layer_add(StationsLayer(self.stationsDf))
        wx.CallAfter(self.statusbar.SetStatusText, 'Show stations')
        self.mapPanel.Refresh()

    def downloadStationsInner(self):
        tempUtils.downloadStationsList()
        wx.CallAfter(self.statusbar.SetStatusText, 'Finished downloading stations')
        self.showStations()

    def downloadSations(self, _):
        wx.CallAfter(self.statusbar.SetStatusText, 'Downloading stations')
        thread = threading.Thread(target=self.downloadStationsInner, name='StationDownload')
        thread.setDaemon(True)
        thread.start()

# =============================================================================

def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1)

# =============================================================================

if __name__ == '__main__':
    setupLogging();

    sys._excepthook = sys.excepthook 
    sys.excepthook = exception_hook    
  
    app = wx.App()
    TempWidget()
    app.MainLoop()

    
