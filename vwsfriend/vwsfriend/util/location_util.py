import requests
from haversine import haversine, Unit, inverse_haversine, Direction
from sqlalchemy import and_

from vwsfriend.model.geofence import Geofence
from vwsfriend.model.location import Location
from vwsfriend.model.charger import Charger, Operator

from weconnect.errors import RetrievalError


def locationFromLatLonWithGeofence(session, latitude, longitude):
    if latitude is None or longitude is None:
        return None
    geofences: Geofence = session.query(Geofence).filter(and_(Geofence.latitude.isnot(None), Geofence.longitude.isnot(None))).all()
    geofenceDistance = [(haversine((latitude, longitude), (geofence.latitude, geofence.longitude), unit=Unit.METERS), geofence) for geofence in geofences]
    geofenceDistance = sorted(geofenceDistance, key=lambda geofence: geofence[0])
    for distance, geofence in geofenceDistance:
        if distance < geofence.radius and geofence.location is not None:
            return geofence.location
    return locationFromLatLon(session, latitude, longitude)


def locationFromLatLon(session, latitude, longitude):
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
        return session.merge(location)
    return None


def amenityFromLatLon(session, latitude, longitude, radius, amenity, withFallback=False):
    northWest = inverse_haversine((latitude, longitude), radius, Direction.NORTHWEST, unit=Unit.METERS)
    southEast = inverse_haversine((latitude, longitude), radius, Direction.SOUTHEAST, unit=Unit.METERS)
    query = {
        'q': f'[{amenity}]',
        'viewbox': f'{northWest[1]},{northWest[0]},{southEast[1]},{southEast[0]}',
        'bounded': 1,
        'namedetails': 1,
        'addressdetails': 1,
        'format': 'json'
    }
    headers = {
        'User-Agent': 'VWsFriend'
    }
    response = requests.get('https://nominatim.openstreetmap.org/search', params=query, headers=headers)
    if response.status_code == requests.codes['ok']:
        places = response.json()
        placesDistance = [(haversine((latitude, longitude), (float(place['lat']), float(place['lon'])), unit=Unit.METERS), place) for place in places]
        placesDistance = sorted(placesDistance, key=lambda geofence: geofence[0])
        for distance, place in placesDistance:
            if distance < radius:
                location = Location(jsonDict=place)
                return session.merge(location)
    if withFallback:
        return locationFromLatLon(session, latitude, longitude)
    return None


def chargerFromLatLonWithGeofence(weConnect, session, latitude, longitude, searchRadius):
    geofences: Geofence = session.query(Geofence).filter(and_(Geofence.latitude.isnot(None), Geofence.longitude.isnot(None))).all()
    geofenceDistance = [(haversine((latitude, longitude), (geofence.latitude, geofence.longitude), unit=Unit.METERS), geofence) for geofence in geofences]
    geofenceDistance = sorted(geofenceDistance, key=lambda geofence: geofence[0])
    for distance, geofence in geofenceDistance:
        if distance < (geofence.radius + searchRadius) and geofence.charger is not None:
            return geofence.charger
    return chargerFromLatLon(weConnect, session, latitude, longitude, searchRadius)


def chargerFromLatLon(weConnect, session, latitude, longitude, searchRadius):
    try:
        chargers = sorted(weConnect.getChargingStations(latitude, longitude, searchRadius=searchRadius).values(), key=lambda station: station.distance.value)
        if len(chargers) > 0:
            return addCharger(session, chargers[0])
    except RetrievalError:
        pass
    return None


def addCharger(session, weConnectCharger):
    charger = Charger(id=weConnectCharger.id.value)
    if weConnectCharger.name.enabled:
        charger.name = weConnectCharger.name.value
    if weConnectCharger.latitude.enabled:
        charger.latitude = weConnectCharger.latitude.value
    if weConnectCharger.longitude.enabled:
        charger.longitude = weConnectCharger.longitude.value
    if weConnectCharger.address.enabled:
        charger.address = str(weConnectCharger.address)
    if weConnectCharger.chargingPower.enabled:
        charger.max_power = weConnectCharger.chargingPower.value
    if weConnectCharger.chargingSpots.enabled:
        charger.num_spots = len(weConnectCharger.chargingSpots)

    charger.operator = Operator(id=weConnectCharger.operator.id.value, name=weConnectCharger.operator.name.value,
                                phone=weConnectCharger.operator.phoneNumber.value)

    return session.merge(charger)
