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


#!wget 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_ljo.csv'
url = 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_ljo.csv'

downloadDir = os.path.expanduser('~/Downloads/Weather')
if not os.path.exists(downloadDir):
    os.makedirs(downloadDir)
    
downloadFile = os.path.join(downloadDir, 'daily_flask_co2_ljo.csv')

if not os.path.exists(downloadFile):
    print('Downloading file - please wait')
    r = requests.get(url, stream=True)
    with open(downloadFile, 'w') as fl:
        for chunk in r.iter_content(chunk_size=4096):
            if chunk: fl.write(chunk)

laJolla = pd.read_csv(downloadFile, 
            header=None, skiprows=69,parse_dates=[0,1], 
            names=['Date', 'Time', 'Excel date', 'Decimal year', 'n', 'Flag', 'cx'])

print(laJolla)
laJolla.plot(x='Date', y='cx')


fig, ax = plt.subplots()

for year in range(1969, 2018):
    yearData = laJolla[(laJolla['Date'] >= pd.Timestamp(datetime.datetime(year, 1, 1))) 
                & (laJolla['Date'] < pd.Timestamp(datetime.datetime(year + 1, 1, 1)))]
    print(year, yearData['cx'].min(), yearData['cx'].max(), yearData['cx'].mean())
    ax.plot(yearData['Date'].apply(lambda p: p.dayofyear), yearData['cx'])


plt.show()
