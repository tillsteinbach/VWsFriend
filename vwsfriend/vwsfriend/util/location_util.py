from vwsfriend.model.location import Location
from vwsfriend.model.charger import Charger, Operator
import requests

from weconnect.errors import RetrievalError


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
