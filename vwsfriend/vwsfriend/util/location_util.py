from vwsfriend.model.location import Location
import requests


def locationFromLatLon(latitude, longitude):
    query = {
        'lat': latitude,
        'lon': longitude,
        'namedetails': 1,
        'format': 'json'
    }
    headers = {
        'User-Agent': 'VWsFriend'
    }

    response = requests.get('https://nominatim.openstreetmap.org/reverse', params=query, headers=headers)
    if response.status_code == requests.codes['ok']:
        location = Location(jsonDict=response.json())
        print(location)