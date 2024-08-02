import time

# ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily


import pandas as pd
import matplotlib.pyplot as plt
from bokeh.plotting import figure, output_file, curdoc, show
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.server.server import Server
from bokeh.layouts import column, row
from bokeh.models import HoverTool, TapTool, CustomJS, Div
from bokeh.events import DoubleTap
import numpy as np
import os
import os.path
import tarfile
import logging
import datetime
import math
import requests
import shutil
import gzip
#from bokeh.util.sampledata import DataFrame

logger = None

#---------------------------------------------------------------------

class TempDaily:
    def readStations(self):
        colspecs = [(0, 11), (12, 19), (21, 29), (31, 36), (38, 39), (41, 70), (72, 74), (76, 78), (80, 84)]
        columnNames =  ["ID", "LATITUDE", "LONGITUDE", "ELEVATION", "STATE", "NAME", "GSN FLAG", "HCN/CRN FLAG", "WMO ID",]

        stationsPath = os.path.expanduser("~/Downloads/Weather/ghcnd-stations.txt")

        if not os.path.exists(stationsPath):
            print(f"Downloading ghcnd-stations.txt")
            with requests.get(url="https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt", stream=True) as result:
                result.raise_for_status()
                print(f"Saving ghcnd-stations.txt")
                with open(stationsPath, 'wb') as fl:
                    shutil.copyfileobj(result.raw, fl)

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
        self.readData(station)

    def periodic(self):
        logger.debug("Periodic callback")
    #---------------------------------------------------------------------

    def getStationDataDly(self, station):
        try:
            interesingElements = ['PRCP', 'TMAX', 'TMIN', 'TAVG']
            stationDF = pd.DataFrame(columns=['StationId', 'Date'] + interesingElements)

            dataPath = os.path.expanduser(f"~/Downloads/Weather/{station.ID}.dly")

            if not os.path.exists(dataPath) or os.path.getmtime(dataPath) < time.time() - 30 * 3600 * 24:
                print(f"Downloading {dataPath}")
                with requests.get(url=f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/gsn/{station.ID}.dly",
                                  stream=True) as result:
                    result.raise_for_status()
                    print(f"Saving {dataPath}")
                    with open(dataPath, 'wb') as fl:
                        shutil.copyfileobj(result.raw, fl)

            with open(dataPath) as stationFile:
                for line in stationFile:
                    line = line if isinstance(line, str) else line.decode('utf-8')
                    element = line[17:21]
                    if element not in interesingElements:
                        continue

                    stationId = line[0:11]
                    startDate = datetime.date(int(line[11:15]), int(line[15:17]), 1)

                    for day in range(1, 32):
                        startField = 21 + (day - 1) * 8
                        value = float(line[startField:startField + 5].strip())
                        if value == -9999:
                            continue
                        fieldDate = startDate.replace(day=day)
                        stationDF.at[fieldDate, element] = value
            return stationDF
        except Exception as e:
            print(f"Exception getting DLY {e}\n")
            return None

    # =================================================================

    def getStationDataCsv(self, station):
        try:
            interesingElements = ['PRCP', 'TMAX', 'TMIN', 'TAVG']
            stationDF = pd.DataFrame(columns=['StationId', 'Date'] + interesingElements)

            dataPath = os.path.expanduser(f"~/Downloads/Weather/{station.ID}..csv.gz")

            if not os.path.exists(dataPath) or os.path.getmtime(dataPath) < time.time() - 30 * 3600 * 24:
                print(f"Downloading {dataPath}")
                with requests.get(url=f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{station.ID}.csv.gz",
                                  stream=True) as result:
                    result.raise_for_status()
                    print(f"Saving {dataPath}")
                    with open(dataPath, 'wb') as fl:
                        shutil.copyfileobj(result.raw, fl)

                with open(dataPath) as stationFile:
                    for line in stationFile:
                        line = line if isinstance(line, str) else line.decode('utf-8')
                        # TODO: Finish

        except Exception as e:
            print(f"Exception getting CSV {e}\n")
            return None

    # =================================================================

    def readData(self, station):
        # station.ID = "IS000009972" # Fix beit dagan
        # station.NAME = "Beit Dagan"

        stationOutputFile = os.path.expanduser(f'~/Downloads/Weather/{station.ID}.csv')
        if os.path.exists(stationOutputFile):
            stationDF = pd.read_csv(stationOutputFile, index_col=0, parse_dates=True)
        else:
            stationDF = self.getStationDataDly(station)

            if stationDF is None:
                stationDF = self.getStationDataCsv(station)

            stationDF.to_csv(stationOutputFile)

        yearlyPrecip = stationDF.groupby(lambda p: p.year)['PRCP'].sum()
        print(yearlyPrecip)
        yearlyPrecipitationPlot = figure(title=f"Precipitation by calendar year: {station.NAME}", x_axis_label='Year', y_axis_label='mm * 100')
        yearlyPrecipitationPlot.line(yearlyPrecip.index, yearlyPrecip)

        monthlyPrecip = stationDF.groupby(lambda p: p.replace(day=1))['PRCP'].sum()
        monthlyPlot = figure(title=f"Precipitation by month: {station.NAME}", x_axis_type="datetime", x_axis_label='Month', y_axis_label='mm * 100')
        monthlyPlot.line(monthlyPrecip.index, monthlyPrecip)

        monthlyComparisonPlot = figure(title=f"Precipitation by month comparison: {station.NAME}", x_axis_label='Month', y_axis_label='mm * 100')

        for year in range(stationDF.index.min().year, stationDF.index.max().year + 1):
            yearData = stationDF[stationDF.index.year == year].groupby(lambda p: p.replace(day=1))['PRCP'].sum()
            monthlyComparisonPlot.line(yearData.index.month, yearData)

        julyMax = stationDF[(stationDF.index.month == 7) & ~stationDF["TMAX"].isna()].groupby(lambda p: p.year)["TMAX"].mean()
        decMin = stationDF[(stationDF.index.month == 12) & ~stationDF["TMIN"].isna()].groupby(lambda p: p.year)["TMIN"].mean()

        julyMax = julyMax.mul(0.1)
        decMin = decMin.mul(0.1)

        tempPlot = figure(title=f"average July/Dec max/min: {station.NAME}", x_axis_label='Year', y_axis_label='C')
        tempPlot.line(julyMax.index, julyMax, legend_label='July Max')
        tempPlot.line(decMin.index, decMin, legend_label='Dec Min')


        stationRow = row(yearlyPrecipitationPlot, monthlyPlot, monthlyComparisonPlot, tempPlot)
        curdoc().add_root(stationRow)


# ID            1-11   Character
# YEAR         12-15   Integer
# MONTH        16-17   Integer
# ELEMENT      18-21   Character
# VALUE1       22-26   Integer
# MFLAG1       27-27   Character
# QFLAG1       28-28   Character
# SFLAG1       29-29   Character
# VALUE2       30-34   Integer
# MFLAG2       35-35   Character
# QFLAG2       36-36   Character
# SFLAG2       37-37   Character
#   .           .          .
#   .           .          .
#   .           .          .
# VALUE31    262-266   Integer
# MFLAG31    267-267   Character
# QFLAG31    268-268   Character
# SFLAG31    269-269   Character

    # ---------------------------------------------------------------------

    def bkapp(self, doc):
        self.readStations()
        plot = self.plotStations()
        plot.on_event(DoubleTap, self.stationClicked)
        self.column = column(plot)
        doc.add_root(self.column)
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
