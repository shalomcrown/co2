#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 27 21:12:44 2018

@author: shalom
"""

import numpy as np
import pandas as pd
import scipy.fftpack
import datetime
import requests
import os
import urllib.parse
import matplotlib.pyplot as plt
from bokeh.plotting import figure, output_file, curdoc, show
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.server.server import Server
from bokeh.layouts import column, row
from bokeh.models import HoverTool, TapTool, CustomJS, Div
from bokeh.events import DoubleTap
from bokeh.io import output_file, show
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.embed import file_html
from bokeh.palettes import Category20_20


scrippsData = [
    ['Alert, NWT, Canada', 'https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_alt.csv', '"'],
    ['Point barrow AL', 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_ptb.csv', '"'],
    ['Station P', 'https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_stp.csv', '"'],
    ['la Jolla' , 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_ljo.csv', '"'],
    ['Baja California Sur, Mexico', 'https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_bcs.csv', '"'],
    ['Mauna Loa',  'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_mlo.csv', '"'],
    ['Cape Kumukahi, Hawaii', 'https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_kum.csv', '"'],
    ['Fanning Island', 'https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_fan.csv', '"'],
    ['American Samoa', 'https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_sam.csv', '"'],
    ['Christmas Island', 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_chr.csv', '"'],
    ['Kermadec Islands, Raoul Island', 'https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_ker.csv', '"'],
    ['Baring head NZ', 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_nzd.csv', '"'],
    ['South pole' , 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_spo.csv', '"'],
]



def downloadFileIfNecessary(url, commentChar):
    downloadDir = os.path.expanduser('~/Downloads/Weather')
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)

    uu = urllib.parse.urlparse(url)
    downloadFile = os.path.join(downloadDir, os.path.basename(uu.path))

    if not os.path.exists(downloadFile):
        print('Downloading file - please wait')
        r = requests.get(url, stream=True)
        with open(downloadFile, 'wb') as fl:
            for chunk in r.iter_content(chunk_size=4096):
                if chunk: fl.write(chunk)

    af = pd.read_csv(downloadFile, 
                header=None, comment=commentChar, parse_dates=[[0,1]], 
                names=['Date', 'Time', 'Excel date', 'Decimal year', 'n', 'Flag', 'cx'])
    af['cx'] = af['cx'].apply(float)
    return af



combinedPlot = figure(title=f"Combined filtered CO2 Readings", x_axis_type="datetime", y_axis_label='ppm', width=1600)
rows = []

for i,data in enumerate(scrippsData):
    name,url,commentChar = data
    df = downloadFileIfNecessary(url, commentChar)
    print((name, df['cx'].min(), df.loc[df['cx'].idxmax()]))
    
    localPlot = figure(title=f"Unfiltered CO2 Readings {name}", x_axis_type="datetime", y_axis_label='ppm')
    localPlot.line(df['Date_Time'], df['cx'])
    df = df[df['cx'] < 420]
    combinedPlot.line(df['Date_Time'], df['cx'], legend_label=name, line_color=Category20_20[i])

    df['day'] = df['Date_Time'].apply(lambda p: p.dayofyear)

    yearPlot = figure(title=f"Year CO2 comparison for {name}", x_axis_label='Day of year', y_axis_label='ppm')
    
    for yearIndex,year in enumerate(range(1969, 2021)):
        yearData = df[(df['Date_Time'] >= pd.Timestamp(datetime.datetime(year, 1, 1))) 
                    & (df['Date_Time'] < pd.Timestamp(datetime.datetime(year + 1, 1, 1)))]
                    
        yearData = yearData.copy()
        yearData = yearData.dropna(axis=1)
        mean = yearData['cx'].mean()
        yearData['cx'] = yearData['cx'] - mean
        std = yearData['cx'].std(skipna=True)
        if std:
            yearData = yearData[(yearData['cx'] < (2 * std)) & (yearData['cx'] > (-2 * std))]
            
        yearPlot.line(yearData['day'], yearData['cx'], line_color=Category20_20[yearIndex % 20])
   
    rows.append(row(localPlot, yearPlot))


rows.insert(0, row(combinedPlot))
show(column(rows))


