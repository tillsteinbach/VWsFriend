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
            charger = Charger(id=chargers[0].id.value)
            if chargers[0].name.enabled:
                charger.name = chargers[0].name.value
            if chargers[0].latitude.enabled:
                charger.latitude = chargers[0].latitude.value
            if chargers[0].longitude.enabled:
                charger.longitude = chargers[0].longitude.value
            if chargers[0].address.enabled:
                charger.address = str(chargers[0].address)
            if chargers[0].chargingPower.enabled:
                charger.max_power = chargers[0].chargingPower.value
            if chargers[0].chargingSpots.enabled:
                charger.num_spots = len(chargers[0].chargingSpots)

            charger.operator = Operator(id=chargers[0].operator.id.value, name=chargers[0].operator.name.value, phone=chargers[0].operator.phoneNumber.value)

            return session.merge(charger)
    except RetrievalError:
        pass
    return None
