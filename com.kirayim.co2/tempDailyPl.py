

# ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily


import pandas as pd
import numpy as np
import os
import os.path
import tarfile
import logging
import webbrowser
import plotly.graph_objects as go
import plotly.express as pe
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

#---------------------------------------------------------------------

class TempDaily:
    def readStations(self):
        colspecs = [(0, 10), (12, 19), (21, 29), (31, 36), (38, 39), (41, 70), (72, 74), (76, 78), (80, 84)]
        columnNames =  ["ID", "LATITUDE", "LONGITUDE", "ELEVATION", "STATE", "NAME", "GSN FLAG", "HCN/CRN FLAG", "WMO ID",]

        stationsPath = os.path.expanduser("~/Downloads/Weather/ghcnd-stations.txt")
        self.stations = pd.read_fwf(stationsPath, colspecs=colspecs, names=columnNames)

    #---------------------------------------------------------------------

    def plotStations(self):

        k = 6378137
        self.stations["x"] = self.stations['LONGITUDE'] * (k * np.pi / 180.0)
        self.stations["y"] = np.log(np.tan((90 + self.stations['LATITUDE']) * np.pi / 360.0)) * k

        mapbox = pe.scatter_mapbox(self.stations, lat="LATITUDE", lon="LONGITUDE", hover_name="NAME", hover_data=["NAME"],
                          color_discrete_sequence=["fuchsia"], zoom=3, height=600)
        mapbox.update_layout(mapbox_style="open-street-map")
        mapbox.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return mapbox

    def stationClicked(self, station, a, b):
        logger.debug(f"Station clicked {station}")

    #---------------------------------------------------------------------

    def readData(self, station):
        dataPath = os.path.expanduser("~/Downloads/Weather/ghcnd_all.tar.gz")
        with tarfile.open(dataPath) as alltar:
            if station:
                stationFile = tarfile.getmember(station + ".dly")
                tarfile.extract(station, "/tmp")
                #TODO: read data..

    def startDash(self, fig):
        app = dash.Dash(__name__)

        app = dash.Dash()
        app.layout = html.Div([
            dcc.Graph(figure=fig, id='map')
        ])

        webbrowser.open('http://127.0.0.1:8050/')
        app.run_server(debug=True, use_reloader=False)


# ---------------------------------------------------------------------


def setupLogging():
    logdir = '/tmp/temps'
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
    temp.readStations()
    fig = temp.plotStations()
    fig.show()
    # webbrowser.open('http://127.0.0.1:8050/')
else:
    logging.basicConfig(level = logging.DEBUG, format ='[%(levelname)s] %(asctime)s  %(filename)s(%(lineno)d)  %(funcName)s %(message)s')
    logger = logging.getLogger('temps')