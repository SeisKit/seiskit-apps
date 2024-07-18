from typing import Any
from urllib import request
import json
from obspy import Catalog, UTCDateTime
from obspy.clients.fdsn import Client
import pandas as pd
import numpy as np
# Ignores performance warnings
from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
simplefilter(action="ignore", category=FutureWarning)
simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)

def GetFDSNEventsLastTwoDays(StartTime : UTCDateTime = None, EndTime: UTCDateTime = None,**kwargs) -> Catalog:
    """_summary_

    Args:
        StartTime (UTCDateTime, optional): _description_. Defaults to None.
        EndTime (UTCDateTime, optional): _description_. Defaults to None.

    Returns:
        Catalog: _description_
    """
    client = Client(timeout=60)

    start_time = UTCDateTime.now() - 48*3600 #1 day ago
    end_time   = UTCDateTime.now()

    min_magnitude = 1.0

    events = client.get_events(starttime=start_time,endtime=end_time,minmagnitude=min_magnitude,**kwargs)

    print("found %s event(s):" % len(events))

    # use this command to print all the events
    #print(events.__str__(print_all=True))

    return events

def FDSN_EventsToDataFrame(Events : Catalog)->pd.DataFrame:
    # store data to dataframe
    #

    feature_list = ['OriginTime', 'Lat', 'Lon', 'depth', 'event_type', 'mag', 'magnitude_type', 'creation_info', 'info']

    df = pd.DataFrame(0, index=np.arange(len(Events)), columns=feature_list)
    for ii in range (0, len(Events)):
        
        df['OriginTime'].loc[ii]        = Events[ii].origins[0].time
        df['Lat'].loc[ii]               = Events[ii].origins[0].latitude
        df['Lon'].loc[ii]               = Events[ii].origins[0].longitude
        df['depth'].loc[ii]             = Events[ii].origins[0].depth    
        df['event_type'].loc[ii]        = Events[ii].event_type   
        df['mag'].loc[ii]               = Events[ii].magnitudes[0].mag     
        df['magnitude_type'].loc[ii]    = Events[ii].magnitudes[0].magnitude_type    
        df['creation_info'].loc[ii]     = Events[ii].origins[0].creation_info 
        df['info'].loc[ii]              = Events[ii].event_descriptions[0].text 

    return df

class RectangularFilter:
    def __init__(self,minLat: float, maxLat : float, minLon : float, maxLon : float) -> None:
        """Rectangular filter class for events searching in AFAD event service

        Args:
            minLat (float): Minimum Latitude
            maxLat (float): Maximum Latitude
            minLon (float): Minimum Longnitude
            maxLon (float): Maximum Longnitude
        """
        self.minLat = minLat
        self.maxLat = maxLat
        self.minLon = minLon
        self.maxLon = maxLon

    def __repr__(self) -> str:
        return f"minlat={self.minLat}&maxlat={self.maxLat}&minlon={self.minLon}&maxlon={self.maxLon}"

class RadialFilter:
    def __init__(self,Lat: float, Lon : float, maxRad : float, minRad : float = None) -> None:
        """Radial filter class for events searching in AFAD event service

        Args:
            Lat (float): Latitude
            Lon (float): Lognitude
            maxRad (float): Max Radial length
            minRad (float, optional): Min radial length. if you dont give this parameters search area become a circle. Defaults to None.
        """
        self.Lat = Lat
        self.Lon = Lon
        self.maxRad = maxRad
        self.minRad = minRad       
    
    def __repr__(self) -> str:
        return f"lat={self.Lat}&lon={self.Lon}&maxrad={self.maxRad}&minrad={self.minRad}"

class DepthFilter:
    def __init__(self,MinDepth: float, MaxDepth : float) -> None:
        """Depth filter class for events searching in AFAD event service

        Args:
            MinDepth (float): Minimum depth
            MaxDepth (float): Maximum depth
        """
        self.MinDepth = MinDepth
        self.MaxDepth = MaxDepth    
    
    def __repr__(self) -> str:
        return f"&mindepth={self.MinDepth}&maxdepth={self.MaxDepth}"
    
class MagnitudeFilter:
    def __init__(self,MgType: str = None, MaxMag : float = None,MinMag : float  = None) -> None:
        """Magnitude filter

        Args:
            MgType (float, optional): Minimum ve maksimum limitleri test etmek için kullanılan Büyüklük türü. Büyük/küçük harfe duyarlıdır. örn:ML Ms mb md Mw Ml MS Mwp. Defaults to None.
            MaxMag (float, optional): Belirtilen maksimum değerden küçük veya eşit büyüklükteki olaylarla sınırlar.. Defaults to None.
            MinMag (float, optional): elirtilen minimum değere eşit veya daha büyük olan depremlerle sınırlar.. Defaults to None.
        """
        self.MgType = MgType
        self.MaxMag = MaxMag    
        self.MinMag = MinMag    
    
    def __repr__(self) -> str:
        return f"&magtype={self.MgType}&maxmag={self.MaxMag}&minmag={self.MinMag}"

def GetAfadEvents(StartTime : UTCDateTime = None, EndTime: UTCDateTime = None,FormatType : str = 'JSON')-> list:
    """Brings the earthquakes that occurred in the last two days

    Args:
        StartTime (datetime, optional): _description_. Defaults to None.
        EndTime (datetime, optional): _description_. Defaults to None.
        FormatType (str, optional): Output formatted type : XML,CSV,KML,GEOJSON,JSON. Defaults to 'JSON'.

    Returns:
        list: _description_
    """

    if StartTime == None or EndTime == None:
        StartTime = UTCDateTime.now() - 48*3600 #1 day ago
        EndTime   = UTCDateTime.now()
    
    url = "https://deprem.afad.gov.tr/apiv2/event/filter?start={}&end={}&orderby=timedesc&format={}".format(StartTime, EndTime, FormatType)
    # url = f"https://deprem.afad.gov.tr/apiv2/event/filter?"+ GeomFilter.__repr__() + f"&mindepth={MinDepth}&maxdepth={MaxDepth}" + f"&start={StartTime}&end={EndTime}" +f"&minmag={MinMag}&maxmag={MaxMag}&magtype={MgType}" + f"&format={FormatType}" 


    with request.urlopen(url, timeout=10) as response:
        if response.getcode() == 200:
            data = response.read()
    data = json.loads(data)
    return data

def GetAfadEvents2(Geom : object  = None, Depth : DepthFilter = None, StartTime : UTCDateTime = None, EndTime: UTCDateTime = None, Magnitude : MagnitudeFilter = None, FormatType : str = 'JSON', OrderBy : str = "timedesc")-> Any:
    """_summary_

    Args:
        Geom (RectangularFilter | RadialFilter, optional): _description_. Defaults to None.
        Depth (DepthFilter, optional): _description_. Defaults to None.
        StartTime (datetime, optional): _description_. Defaults to None.
        EndTime (datetime, optional): _description_. Defaults to None.
        Magnitude (MagnitudeFilter, optional): _description_. Defaults to None.
        FormatType (str, optional): _description_. Defaults to 'JSON'.
        OrderBy (str, optional): _description_. Defaults to 'timedesc'.

    Returns:
        Any: _description_
    """
    url = "https://deprem.afad.gov.tr/apiv2/event/filter?"

    if StartTime == None or EndTime == None:
        StartTime = UTCDateTime.now() - 24*3600 #1 day ago
        EndTime   = UTCDateTime.now()

    if Geom != None:
        url = url + Geom.__repr__()
    if Depth != None:
        url += Depth.__repr__()
    url += "&start={}&end={}".format(StartTime,EndTime)
    if Magnitude != None:
        url += Magnitude.__repr__()
    url += "&orderby={}".format(OrderBy)
    url += "&format={}".format(FormatType)

    with request.urlopen(url, timeout=10) as response:
        if response.getcode() == 200:
            data = response.read()
    data = json.loads(data)
    return data

def GetAfadEventsByEventId(EventId : int,FormatType : str = 'JSON') -> Any:
    """_summary_

    Args:
        EventId (int): _description_
        FormatType (str, optional): _description_. Defaults to 'JSON'.

    Returns:
        Any: _description_
    """
    url = f"https://deprem.afad.gov.tr/apiv2/event/filter?eventid={EventId}"
    with request.urlopen(url, timeout=10) as response:
        if response.getcode() == 200:
            data = response.read()
    return data

def GetUSGSEvents(Geom : object  = None, Depth : DepthFilter = None, StartTime : UTCDateTime = None, EndTime: UTCDateTime = None, Magnitude : MagnitudeFilter = None, FormatType : str = 'geojson')-> Any:
    """_summary_

    Args:
        Geom (RectangularFilter | RadialFilter, optional): _description_. Defaults to None.
        Depth (DepthFilter, optional): _description_. Defaults to None.
        StartTime (datetime, optional): _description_. Defaults to None.
        EndTime (datetime, optional): _description_. Defaults to None.
        Magnitude (MagnitudeFilter, optional): _description_. Defaults to None.
        FormatType (str, optional): _description_. Defaults to 'geojson'.

    Returns:
        Any: _description_
    """
    # query methods
    # Formats = csv,geojson(callback methods returns JSONP),kml,quakeml,text,xml
    # Time = starttime,endtime,updatedafter
    # Location = Rectangle(minlatitude,minlongitude,maxlatitude,maxlongitude),Circle(latitude,longitude,maxradius,maxradiuskm)
    # Other = catalog,eventid,limit,maxdepth,maxmagnitude,mindepth,minmagnitude,orderby
    # example ==> url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2014-01-01&starttime=2014-01-02"

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?"
    

    if StartTime == None or EndTime == None:
        StartTime = UTCDateTime.now() - 24*3600 #1 day ago
        EndTime   = UTCDateTime.now()

    url += "format={}&".format(FormatType)
    url += "start={}&end={}&".format(StartTime,EndTime)
    if Geom != None:
        if type(Geom) == RectangularFilter:
            url += "minlatitude={}&minlongitude={}&maxlatitude={}&maxlongitude={}&".format(Geom.minLat,Geom.minLon,Geom.maxLat,Geom.maxLon)
        if type(Geom) == RadialFilter:
            url += "latitude={}&longitude={}&maxradius={}&".format(Geom.Lat,Geom.Lon,Geom.maxRad)
    if Depth != None:
        url += "mindepth={}&maxdepth={}&".format(Depth.MinDepth,Depth.MaxDepth)
    
    if Magnitude != None:
        url += "minmagnitude={}&maxmagnitude={}&".format(0,Magnitude.MaxMag)
    

    with request.urlopen(url, timeout=10) as response:
        if response.getcode() == 200:
            data = response.read()
    data = json.loads(data)
    for ii in range (0, len(data['features'])):
        data['features'][0]['properties']['depth'] = data['features'][ii]['geometry']['coordinates'][2]
    return data

def USGS_EventsDataToDataFrame(data : dict)->pd.DataFrame:
    feature_list = ['OriginTime', 'Lat', 'Lon', 'depth', 'event_type', 'mag', 'magnitude_type', 'place', 'url', 'urldetails']
    df = pd.DataFrame(0, index=np.arange(len(data['features'])), columns=feature_list)
    for ii in range (0, len(data['features'])):
            df['OriginTime'].loc[ii] = pd.to_datetime(data['features'][ii]['properties']['time'], unit='ms').strftime('%y/%m/%d %H:%M:%S')
            df['Lat'].loc[ii]               = data['features'][ii]['geometry']['coordinates'][0]
            df['Lon'].loc[ii]               = data['features'][ii]['geometry']['coordinates'][1]
            df['depth'].loc[ii]             = data['features'][ii]['geometry']['coordinates'][2]   
            df['event_type'].loc[ii]        = data['features'][ii]['properties']['type']
            df['mag'].loc[ii]               = data['features'][ii]['properties']['mag']
            df['magnitude_type'].loc[ii]    = data['features'][ii]['properties']['magType']    
            df['place'].loc[ii]             = data['features'][ii]['properties']['place']
            df['url'].loc[ii]               = data['features'][ii]['properties']['url']
            df['urldetails'].loc[ii]        = data['features'][ii]['properties']['detail']
    return df


# if __name__ == "__main__":
    
#     # from obspy import UTCDateTime
#     # start_time  = UTCDateTime.now() - 24*3600 #1 day ago
#     # end_time    = UTCDateTime.now()
#     # recFilter   = RectangularFilter(minLat=39,maxLat=41,minLon=32,maxLon=34)
#     # radFilter   = RadialFilter(Lat=33,Lon=40,maxRad=100_000,minRad=50_000)
#     # depthFilter = DepthFilter(MinDepth=1,MaxDepth=8)
#     # mgFilter    = MagnitudeFilter('mb',7,1)
#     # Data        = GetAfadEventsLastTwoDays()
#     # event       = GetAfadEventsByEventId(EventId=632764,FormatType='GEOJSON')
#     # print(event)
#     # df          = GetFDSNEventsLastTwoDays()
#     # print(df)
#     # events = GetUSGSEvents(Geom=recFilter)
    # eventData = GetUSGSEvents()
    # df_USGS = USGS_EventsDataToDataFrame(eventData)
    # print(df_USGS)
