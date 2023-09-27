
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import os.path
import tarfile
import logging
import datetime
import ftplib

logger = logging.getLogger('tempwx')


# ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt


noaaFtp = 'ftp.ncdc.noaa.gov'
noaaDaily = '/pub/data/ghcn/daily/'
cachePath = os.path.expanduser("~/Downloads/Weather/")

def stationsPath():
    return os.path.join(cachePath, "ghcnd-stations.txt")


def readStations():
    '''
    Read station data from ghcnd-stations.txt
    Returns dataframe with stations
    '''
    colspecs = [(0, 11), (12, 19), (21, 29), (31, 36), (38, 39), (41, 70), (72, 74), (76, 78), (80, 84)]
    columnNames =  ["ID", "LATITUDE", "LONGITUDE", "ELEVATION", "STATE", "NAME", "GSN FLAG", "HCN/CRN FLAG", "WMO ID",]

    df = pd.read_fwf(stationsPath(), colspecs=colspecs, names=columnNames)
    
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'])
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'])
    df['ELEVATION'] = pd.to_numeric(df['ELEVATION'])
    
    return df

        
def hasStationsList():
    return os.path.exists(stationsPath())


def downloadStationsList():
    ftp = ftplib.FTP(noaaFtp)
    ftp.login()
    ftp.cwd(noaaDaily)
    os.makedirs(cachePath, exist_ok = True)
    ftp.retrbinary("RETR " + "ghcnd-stations.txt", open(stationsPath(), 'wb').write)


def getStationData(station):
    stationOutputFile = os.path.expanduser(f'~/Downloads/Weather/{station.ID}.csv')
    if os.path.exists(stationOutputFile):
        stationDF = pd.read_csv(stationOutputFile, index_col=0, parse_dates=True)
    else:
        interesingElements = ['PRCP', 'TMAX', 'TMIN', 'TAVG']
        stationDF = pd.DataFrame(columns=['StationId', 'Date'] + interesingElements)
        dataPath = os.path.expanduser("~/Downloads/Weather/ghcnd_all.tar.gz")
        with tarfile.open(dataPath) as alltar:
            stationFileTarInfo = alltar.getmember(f'ghcnd_all/{station.ID}.dly')
            with alltar.extractfile(stationFileTarInfo) as stationFile:
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
        stationDF.to_csv(stationOutputFile)

    yearlyPrecip = stationDF.groupby(lambda p: p.year)['PRCP'].sum()
    monthlyPrecip = stationDF.groupby(lambda p: p.replace(day=1))['PRCP'].sum()
    monthlyComparison = []

    indexSeries = stationDF.index.to_series()

    for year in range(stationDF.index.min().year, stationDF.index.max().year + 1):
        start = datetime.datetime(year=year, month=1, day=1)
        stop = datetime.datetime(year=year + 1, month=1, day=1)

        if start in indexSeries and stop in indexSeries:
            yearData = stationDF[indexSeries.between(start, stop)].groupby(lambda p: p.replace(day=1))['PRCP'].sum()
            monthlyComparison.append(yearData)

    print(yearlyPrecip)
    return yearlyPrecip, monthlyPrecip, monthlyComparison