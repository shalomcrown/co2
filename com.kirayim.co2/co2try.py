#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 27 21:12:44 2018

@author: shalom
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.fftpack
import datetime
import requests
import os
import urlparse


scrippsData = [
    ['la Jolla' , 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_ljo.csv', '"'],
    ['South pole' , 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_spo.csv', '"'],
    ['Mauna Loa',  'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_mlo.csv', '"'],
    ['Point barrow AL', 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_ptb.csv', '"'],
    ['Christmas Island', 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_chr.csv', '"']
]





def downloadFileIfNecessary(url, commentChar):
    downloadDir = os.path.expanduser('~/Downloads/Weather')
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)

    uu = urlparse.urlparse(url)
    downloadFile = os.path.join(downloadDir, os.path.basename(uu.path))

    if not os.path.exists(downloadFile):
        print('Downloading file - please wait')
        r = requests.get(url, stream=True)
        with open(downloadFile, 'w') as fl:
            for chunk in r.iter_content(chunk_size=4096):
                if chunk: fl.write(chunk)

    af = pd.read_csv(downloadFile, 
                header=None, comment=commentChar, parse_dates=[[0,1]], 
                names=['Date', 'Time', 'Excel date', 'Decimal year', 'n', 'Flag', 'cx'])
    af['cx'] = af['cx'].apply(float)
    return af


fig, ax = plt.subplots()

for name,url,commentChar in scrippsData:
    df = downloadFileIfNecessary(url, commentChar)
    print(name, df['cx'].min(), df.ix[df['cx'].argmax()])
    df.plot(x='Date_Time', y='cx', label=name) # Before any filtering
    df = df[df['cx'] < 420]    
    ax.plot(df['Date_Time'], df['cx'], label=name)
#
#    for year in range(1969, 2018):
#        yearData = df[(df['Date_Time'] >= pd.Timestamp(datetime.datetime(year, 1, 1))) 
#                    & (df['Date_Time'] < pd.Timestamp(datetime.datetime(year + 1, 1, 1)))]
#        yearData.


ax.set_ylabel("CO2 ppm")
ax.set_xlabel('Date')
ax.legend(loc='best')





#for year in range(1969, 2018):
#    yearData = laJolla[(laJolla['Date'] >= pd.Timestamp(datetime.datetime(year, 1, 1))) 
#                & (laJolla['Date'] < pd.Timestamp(datetime.datetime(year + 1, 1, 1)))]
#                
#    
#    print(year, yearData['cx'].min(), yearData['cx'].max(), yearData['cx'].mean())
#    ax.plot(yearData['Date'].apply(lambda p: p.dayofyear), yearData['cx'])
#
#ax.set_xlabel("Day of year")
#ax.set_ylabel("CO2 ppm")
#ax.set_title("Seasonal Daily CO2 ppm At La Jolla for 1969 to 2018")
#
plt.show()
