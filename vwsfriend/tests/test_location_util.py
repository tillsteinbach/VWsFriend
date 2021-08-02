
from vwsfriend.util.location_util import locationFromLatLon

def test_locationFromLatLon():
    location = locationFromLatLon(latitude=53.60853453781239, longitude=10.19093520255688)
    assert location is not None
