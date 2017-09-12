'''
Created on Sep 12, 2017

@author: theo
'''
import os
import gdal, osr
import numpy as np
import datetime
from datetime import timedelta
from webob.exc import HTTPError
from acacia.data.generators.generic import GenericCSV
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

class GPM:
    """ Download tiles and time series from GPM opendap server """
    
    class Template:
        """ Helper for formatting urls and filenames """

        # format strings
        day = '{name}_{west:04}{north:04}{east:04}{south:04}_{date:%Y%m%d}.tif'
        m30 = '{name}_{west:04}{north:04}{east:04}{south:04}_{time:%Y%m%d%M%H}.tif'
        urlday = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGDL.04/{year}/{month:02}/3B-DAY-L.MS.MRG.3IMERG.{year}{month:02}{day:02}-S000000-E235959.V04.nc4'
        urlm30 = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGHHL.04/{year}/{doy:03}/3B-HHR-L.MS.MRG.3IMERG.{year}{month:02}{day:02}-S{hour:02}{start:04}-E{hour:02}{end:04}.0000.V04B.HDF5'

        # regex pattern for cache rasters
        pattern = r'(?P<name>\w+)_(?P<west>\d{4})(?P<north>\d{4})(?P<east>\d{4})(?P<south>\d{4})_(?P<date>\d+)\.tif'
        
        @classmethod
        def url_day(self,date):
            """ return url for daily accumulated values (late run) """
            return self.urlday.format(year = date.year, month = date.month, day = date.day)
        
        @classmethod
        def url_m30(self,time):
            """ return url for 30 minute values (late run) """
            #determine day-of-year and start/end in minutes
            doy = (time - datetime.date(time.year,1,1)).days + 1
            start = 0 if time.minute < 30 else 3000
            end = 2959 if time.minute < 30 else 5959
            return self.urlm30.format(year = time.year, doy = doy, month = time.month, day = time.day, hour=time.hour, start=start,end=end)

        @classmethod
        def name_day(self, view, date, name='precipitationCal'):
            """ return name for tile with daily values"""
            left,bottom,right,top = GPM.lbrt(view)
            return self.day.format(
                name=name,
                west=left,
                north=top,
                east=right,
                south=bottom,
                date=date)
    
        @classmethod
        def name_m30(self, view, time, name='precipitationCal'):
            """ return name for tile with 30 minute values """
            left,bottom,right,top = GPM.lbrt(view)
            return self.m30.format(
                name=name,
                west=left,
                north=top,
                east=right,
                south=bottom,
                time=time)
            
        @classmethod
        def parse(self,name):
            import re
            m = re.match(self.pattern, name)
            return m.groupdict() if m else {}

    def __init__(self,**kwargs):
        self.session = None
        self.dataset = None
        self.cache = kwargs.get('cache',None)
        self.username= kwargs.get('username',None)
        self.password = kwargs.get('password',None)
        self.view = kwargs.get('view',None)
             
    def start_session(self,url):
        from pydap.cas.urs import setup_session
        self.session = setup_session(self.username,self.password,check_url=url)
        return self.session
                
    def open(self, url):
        """ Open url and return dataset """
        from pydap.client import open_url
        if not self.session:
            self.start_session(url)
        self.dataset = open_url(url, session=self.session)
        return self.dataset

    def close(self):
        """ close session and dataset """
        self.session = None
        self.dataset = None
    
    @classmethod
    def rowcol(self,lon,lat):
        """ transform (lon,lat) to (row,col) coordinates to index dataset """ 
        return int((lon + 180) * 10), int((lat + 90) * 10)

    @classmethod
    def lbrt(self,view):
        """ transform view to dataset coordinates """ 
        west,south,east,north = view
        left,bottom = self.rowcol(west,south)
        right,top = self.rowcol(east,north)
        return (left,bottom,right,top)

    def download_tile(self,view,filename):
        """ download and save view of current dataset as geotiff """

        left,bottom,right,top = GPM.lbrt(view)
        
        # download the precipitation dataset
        tile = self.dataset.precipitationCal[left:right,bottom:top]

        # swap cols and rows
        data = tile.data.astype(np.float32).transpose()
        
        # ensure cache folder exists
        if not os.path.exists(self.cache):
            os.makedirs(self.cache)

        path = os.path.join(self.cache, filename)
        if os.path.exists(path):
            # delete existing output file
            os.remove(path)

        # create new output file
        width, height = tile.shape
        tif = gdal.GetDriverByName('GTiff').Create(path, width, height, 1, gdal.GDT_Float32)

        # setup SRS (WGS84)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        wgs84 = srs.ExportToWkt()
        tif.SetProjection(wgs84)
         
        # setup geotransform
        tif.SetGeoTransform([view[0],0.1,0,view[1],0,0.1])

        # write data to file
        tif.GetRasterBand(1).WriteArray(data)

    def find_daily(self, date, lon, lat):
        """ find the file in cache from lonlat coordinates """
        
        date = datetime.datetime(date.year,date.month,date.day) #ignore time
        logger.debug('searching cache for daily file at {} {} {}'.format(lon, lat, date.date()))
        x,y = self.rowcol(lon, lat)
        for path, dirs, files in os.walk(self.cache):
            for name in sorted(files):
                if not name.endswith('tif'):
                    continue
                components = self.Template.parse(name)
                if not components:
                    continue
                dt = components['date']
                if len(dt) == 8:
                    dt = datetime.datetime.strptime(dt,'%Y%m%d')
                else:
                    continue
                if date != dt:
                    continue 
                left = int(components['west'])
                if x < left:
                    continue
                right = int(components['east'])
                if x > right:
                    break
                top = int(components['north'])
                if y > top:
                    continue
                bottom = int(components['south'])
                if y < bottom:
                    continue
                
                logger.debug('found {}/{}'.format(path, name))
                return (path, name)
        return None
    
    def download_value(self,lon,lat):
        """ download single value at (lon,lat) from current open dataset """

        x,y = GPM.rowcol(lon,lat)
        
        # query the precipitation dataset
        pix = self.dataset.precipitationCal[x,y]
        
        return pix.data[0,0]

    def get_cached_value(self, filename, lon, lat):
        """ get single value from cache """
        path = os.path.join(self.cache, filename)
        ds = gdal.OpenShared(path)
        fwd = ds.GetGeoTransform()
        inv = gdal.InvGeoTransform(fwd)
        x,y = gdal.ApplyGeoTransform(inv,lon,lat)
        x = int(max(0,min(ds.RasterXSize-1,x)))
        y = int(max(0,min(ds.RasterYSize-1,y)))
        value = ds.GetRasterBand(1).ReadAsArray(x,y,1,1)
        return value[0][0]

    def download_daily_value(self, date, lon, lat):
        """ download daily value from dap server """
        url = GPM.Template.url_day(date)
        print date, url
        try:
            self.open(url)
            return self.download_value(lon, lat)
        except HTTPError as e:
            msg = unicode(e).split('\n')
            print msg[0] 
        return None

    def download_halfhourly_value(self, time, lon, lat):
        """ download daily value from dap server """
        url = GPM.Template.url_hh(time)
        print time, url
        try:
            self.open(url)
            return self.download_value(lon, lat)
        except HTTPError as e:
            msg = unicode(e).split('\n')
            print msg[0] 
        return None

    def get_daily_value(self, date, lon, lat):
        """ get single value from cache, download tile if cached file does not exist """
        found = self.find_daily(date, lon, lat)
        if found:
            _path, name = found
            logger.debug('Retrieving value from cache')
            return self.get_cached_value(name, lon, lat)
        else:
            try:
                name, success = self.update_daily_tile(date)
                if success:
                    return self.get_cached_value(name, lon, lat)
            except Exception as e:
                msg = unicode(e).split('\n')
                logger.error(msg[0])
        return self.download_daily_value(date, lon, lat)
        
    def update_daily_tile(self, date, view=None):
        """ update single raster in cache """
        view = view or self.view
        assert view, 'No view defined'
        filename = GPM.Template.name_day(view, date)
        path = os.path.join(self.cache,filename)
        if not os.path.exists(path):
            url = GPM.Template.url_day(date)
            try:
                logger.debug('Contacting {}'.format(url))
                self.open(url)
                logger.debug('Downloading tile')
                self.download_tile(view, filename)
                logger.debug('Tile saved as {}'.format(filename))
                return (filename,True)
            except HTTPError as e:
                msg = unicode(e).split('\n')
                logger.error(msg[0])
        return (filename,False) 
            
    def update_halfhourly_tile(self, time, view=None):
        view = view or self.view
        assert view, 'No view defined'
        filename = GPM.Template.name_m30(view, time)
        path = os.path.join(self.cache,filename)
        if not os.path.exists(path):
            url = GPM.Template.url_m30(time)
            try:
                logger.debug('Contacting {}'.format(url))
                self.open(url)
                logger.debug('Downloading tile')
                self.download_tile(view, filename)
                logger.debug('Tile saved as {}'.format(filename))
                return (filename,True)
            except HTTPError as e:
                msg = unicode(e).split('\n')
                logger.error(msg[0])
        return (filename,False) 
            
    def process(self, start, stop, delta, callback, **kwargs):
        date = start
        while date < stop:
            callback(date,**kwargs)
            date = date + delta

    def iter(self, start, stop, delta, callback, **kwargs):
        date = start
        while date < stop:
            yield date,callback(date,**kwargs)
            date = date + delta

    def download_daily_values(self, start, stop, lon, lat):
        """ download daily values from dap server """     
        return self.process(lon, lat, start, stop, timedelta(days=1), self.download_daily_value,lon=lon,lat=lat)

    def download_halfhourly_values(self, start, stop, lon, lat):
        """ download half hourly values from dap server """
        return self.process(lon, lat, start, stop, timedelta(minutes=30), self.download_halfhourly_value,lon=lon,lat=lat)
                        
    def update_daily_tiles(self, start, stop, view=None):
        """ update cache of daily views """
        self.process(start, stop, timedelta(days=1),self.update_daily_tile,view=view)

    def update_halfhourly_tiles(self, start, stop, view=None):
        """ update cache of 30 minute views """
        self.process(start, stop, timedelta(minutes=30),self.update_halfhourly_tile,view=view)
            
            
class Daily(GenericCSV):
    """ retrieves daily timeseries from GPM and stores as csv """
    
    url = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGDL.04'
   
    def download(self, **kwargs):
        from pytz import utc
        debilt = (5.177,52.101) # lonlat
        lon,lat = kwargs.get('lonlat',debilt)
        defview = (lon-1,lat-1,lon+1,lat+1)
        stop = utc.localize(datetime.datetime.today()-timedelta(days=1))
        start = kwargs.get('start', None) or stop-timedelta(days=7) # retrieve last week by default
        username = kwargs.get('username',None)
        password = kwargs.get('password',None)
        
        gpm = GPM(cache=settings.GPM_CACHE,
                  username=username,
                  password=password,
                  view=kwargs.get('view',defview))
        contents = ['date,precipitation']
        for date,value in gpm.iter(start, stop, timedelta(days=1), gpm.get_daily_value, lon=lon, lat=lat):
            contents.append('{:%Y-%m-%d},{}'.format(date,value or ''))
        
        filename = 'gpm_{lon:04d}{lat:04d}_{start:%Y%m%d}{stop:%Y%m%d}.csv'.format(lon=int(lon*10),lat=int(lat*10),start=start,stop=stop)
        filename = kwargs.get('filename', filename)
        result = {filename: '\n'.join(contents)}
        if 'callback' in kwargs:
            callback = kwargs['callback']
            callback(result)
        return result

if __name__ == '__main__':
    start = datetime.datetime(2017,9,1)
    stop = datetime.datetime(2017,9,11)
    akokorio = (33.84766944, 1.858688889)
    lon,lat = akokorio
    cache = '/home/theo/src/gpm/gpm/gpm/data/flip'
    view = (29,-2,35,5)
    options = {
        'cache': cache,
        'view': view,
        'username': 'tkleinen',
        'password': 'pw4EarthData'
    }
    gpm = GPM(**options)
#    print gpm.lbrt(view)
#    print gpm.rowcol(lon, lat)
#     name = gpm.find_daily(start, lon, lat)
    
#    name = GPM.Template.name_day(view, start)
#     components = GPM.Template.parse(name)
#     print components
    
    gpm.update_daily_tiles(start, stop)
    with open(os.path.join(cache,'akokorio-cache.csv'),'w') as csv:
        csv.write('date,precipitation\n')
        lon,lat = akokorio
        for date, value in gpm.iter(start, stop, timedelta(days=1), gpm.get_daily_value, lon=lon, lat=lat):
            csv.write('{:%Y-%m-%d},{:2f}\n'.format(date,value))

    with open(os.path.join(cache,'akokorio-server.csv'),'w') as csv:
        csv.write('date,precipitation\n')
        lon,lat = akokorio
        for date, value in gpm.iter(start, stop, timedelta(days=1), gpm.download_daily_value, lon=lon, lat=lat):
            csv.write('{:%Y-%m-%d},{:2f}\n'.format(date,value))
             
    
    #gpm.update_halfhourly(view, start, stop)
    