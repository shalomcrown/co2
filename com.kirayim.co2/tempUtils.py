
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

    return pd.read_fwf(stationsPath(), colspecs=colspecs, names=columnNames)

        
def hasStationsList():
    return os.path.exists(stationsPath())


def downloadStationsList():
    ftp = ftplib.FTP(noaaFtp)
    ftp.login()
    ftp.cwd(noaaDaily)
    os.makedirs(cachePath, exist_ok = True)
    ftp.retrbinary("RETR " + "ghcnd-stations.txt", open(stationsPath(), 'wb').write)
