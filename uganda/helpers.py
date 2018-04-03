# -*- coding: utf-8 -*-
'''
Created on Jul 29, 2017

@author: theo
'''
from django.conf import settings

class Latest(object):

    @classmethod
    def info(cls,loc):
        """ returns a dict with latest information from a location using available timeseries """
        def last(s):
            try:
                return s.datapoints.latest('date').value
            except:
                return None
        #CSV files:
        csv = loc.datasource_set.filter(generator__classname__icontains='CSV').first()
        stop = csv.stop() if csv else None
        tahmo = loc.datasource_set.filter(generator__classname__icontains='Tahmo').first()
        stop = tahmo.stop() if tahmo else stop
        #bat = loc.series_set.filter(name__istartswith='bat').first()
        #level = loc.series_set.filter(name__istartswith='gauge').first()
        temp  = loc.series_set.filter(name__istartswith='temp').first()
        precipitation = loc.series_set.filter(name__istartswith='prec').first()
        #ec  = loc.series_set.filter(name__istartswith='EC').first()
        battery = None #last(bat)
        url = None if battery is None else '{url}bat{level}.png'.format(url=settings.STATIC_URL, level=int(battery/20))
        return {'date': stop,
                'battery': battery,
                'level': '-',
                'precipitation': last(precipitation),
                'temp': last(temp),
                'ec': '-',
                'battery_url': url, 
                }
