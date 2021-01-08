

# ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily


import pandas as pd
import matplotlib.pyplot as plt
from bokeh.plotting import figure, output_file, curdoc, show
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.server.server import Server
from bokeh.layouts import column
from bokeh.models import HoverTool, TapTool, CustomJS, Div
from bokeh.events import DoubleTap
import numpy as np
import os
import os.path
import tarfile
import logging

logger = None

#---------------------------------------------------------------------

class TempDaily:
    def readStations(self):
        colspecs = [(0, 10), (12, 19), (21, 29), (31, 36), (38, 39), (41, 70), (72, 74), (76, 78), (80, 84)]
        columnNames =  ["ID", "LATITUDE", "LONGITUDE", "ELEVATION", "STATE", "NAME", "GSN FLAG", "HCN/CRN FLAG", "WMO ID",]

        stationsPath = os.path.expanduser("~/Downloads/Weather/ghcnd-stations.txt")
        self.stations = pd.read_fwf(stationsPath, colspecs=colspecs, names=columnNames)

    #---------------------------------------------------------------------

    def plotStations(self):
        output_file("/tmp/stations.html")

        tile_provider = get_provider(CARTODBPOSITRON)

        # range bounds supplied in web mercator coordinates
        hover = HoverTool(tooltips=[("Station", "@NAME"), ("ID", "@ID")])
        p = figure(x_range=(-2000000, 6000000), y_range=(-1000000, 7000000), x_axis_type="mercator", y_axis_type="mercator", width=1200)

#         taptool = TapTool()
#         taptool.callback = CustomJS.from_py_func(self.stationClicked)

        p.add_tools(hover)
#         p.add_tools(taptool)
        p.add_tile(tile_provider)
        p.on_event('')

        k = 6378137
        self.stations["x"] = self.stations['LONGITUDE'] * (k * np.pi / 180.0)
        self.stations["y"] = np.log(np.tan((90 + self.stations['LATITUDE']) * np.pi / 360.0)) * k

        p.scatter('x', 'y', source=self.stations)
        return p

    def stationClicked(self, doubleTap):
        logger.debug(f"Station clicked {doubleTap.x},{doubleTap.y}")
        pythagoras = (self.stations["x"] - doubleTap.x) ** 2 + (self.stations["y"] - doubleTap.y) ** 2
        station = self.stations.iloc[pythagoras.idxmin()]
        logger.debug(station) 

    def periodic(self):
        logger.debug("Periodic callback")
    #---------------------------------------------------------------------

    def readData(self, station):
        dataPath = os.path.expanduser("~/Downloads/Weather/ghcnd_all.tar.gz")
        with tarfile.open(dataPath) as alltar:
            if station:
                stationFile = tarfile.getmember(station + ".dly")
                tarfile.extract(station, "/tmp")
                #TODO: read data..

    # ---------------------------------------------------------------------

    def bkapp(self, doc):
        self.readStations()
        plot = self.plotStations()
        plot.on_event(DoubleTap, self.stationClicked)
        doc.add_root(column(plot))
        # , Div("<h1>Double click a station to get data</h1>")

# ---------------------------------------------------------------------


def setupLogging():
    logdir = '/tmp/temps'
    global logger
    logger = logging.getLogger('temps')
    logger.setLevel(logging.DEBUG)
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    handler = logging.handlers.RotatingFileHandler(os.path.join(logdir, 'temps.log'),
                                                   backupCount=30, maxBytes=1024 * 1024 * 10)

    formatter = logging.Formatter('[%(levelname)s] %(asctime)s  %(filename)s(%(lineno)d)  %(funcName)s %(message)s')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    outhandler = logging.StreamHandler()
    outhandler.setLevel(logging.DEBUG)
    outhandler.setFormatter(formatter)
    logger.addHandler(outhandler)

# ---------------------------------------------------------------------


if __name__ == '__main__':
    setupLogging()
    temp = TempDaily()
    print('Opening Bokeh application on http://localhost:5006/')
    server = Server({'/' : temp.bkapp})
    server.start()
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    logging.basicConfig(level = logging.DEBUG, format ='[%(levelname)s] %(asctime)s  %(filename)s(%(lineno)d)  %(funcName)s %(message)s')
    logger = logging.getLogger('temps')
    
    