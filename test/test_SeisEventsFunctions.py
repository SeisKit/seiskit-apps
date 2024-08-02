import pytest
from applications.seisEvents.SeisEventsFunctions import GetFDSNEventsLastTwoDays,RectangularFilter,RadialFilter,DepthFilter,MagnitudeFilter,GetAfadEventsLastTwoDays2,GetAfadEventsByEventId,GetAfadEventsLastTwoDays
from obspy import UTCDateTime

# Global Variables
start_time = UTCDateTime.now() - 24*3600 #1 day ago
end_time   = UTCDateTime.now()

@pytest.fixture(scope="class")
def Rectang():
    return RectangularFilter(minLat=39,maxLat=41,minLon=32,maxLon=34)

@pytest.fixture(scope="class")
def Radial():
    return RadialFilter(Lat=33,Lon=40,maxRad=100_000,minRad=50_000)

@pytest.fixture(scope="class")
def Depth():
    return DepthFilter(MinDepth=1,MaxDepth=8)

@pytest.fixture(scope="class")
def Magnitude():
    return MagnitudeFilter('mb',7,1)

def test_GetFDSNEventsLastTwoDays() ->None:
    pass

def test_GetAfadEventsLastTwoDays() ->None:
    assert type(GetAfadEventsLastTwoDays()) == list
    

def test_GetAfadEventsLastTwoDays2(Rectang,Radial,Depth,Magnitude) ->None:
    assert type(GetAfadEventsLastTwoDays2(Rectang)) == list

def test_GetAfadEventsByEventId() ->None:
    pass