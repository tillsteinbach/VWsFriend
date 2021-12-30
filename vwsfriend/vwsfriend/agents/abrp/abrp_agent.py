import logging
import json
from requests import Session, codes
from requests.structures import CaseInsensitiveDict
from requests import RequestException

from weconnect.elements.vehicle import Vehicle
from weconnect.elements.charging_status import ChargingStatus

from vwsfriend.__version import __version__

LOG = logging.getLogger("VWsFriend")

API_BASE_URL = 'https://api.iternio.com/1/'
VWSFRIEND_IDENTIFIER = '6225724a-65fb-4d4c-9ac5-d7dff2b78c1d'

HEADER = CaseInsensitiveDict({'accept': 'application/json',
                              'user-agent': f'VWsFriend ({__version__})',
                              'accept-language': 'en-en',
                              'Authorization': f'APIKEY {VWSFRIEND_IDENTIFIER}'})


class ABRPAgent():
    def __init__(self, weConnectVehicle: Vehicle, tokenfile: str):
        self.weConnectVehicle = weConnectVehicle
        self.__session: Session = Session()
        self.__session.headers = HEADER
        self.__userTokens: list[tuple[str, str]] = []

        self.telemetryData: dict = {}
        self.tokenfile: str = tokenfile
        try:
            self.readTokens(tokenfile)
        except FileNotFoundError:
            pass

    @property
    def userTokens(self):
        return self.__userTokens

    @userTokens.setter
    def userTokens(self, userTokens):
        self.__userTokens = userTokens
        self.persistTokens(self.tokenfile)

    def persistTokens(self, tokenfile):
        if tokenfile:
            try:
                with open(tokenfile, 'w') as file:
                    json.dump(self.__userTokens, fp=file)
                LOG.info('Writing tokenfile %s', tokenfile)
            except ValueError as err:  # pragma: no cover
                LOG.info('Could not write abrp tokenfile %s (%s)', tokenfile, err)

    def readTokens(self, tokenfile):
        with open(tokenfile, 'r') as file:
            tokens = json.load(fp=file)
            self.__userTokens = tokens
        LOG.info('Reading abrp tokenfile %s', tokenfile)

    def updateTelemetry(self):
        for account, token in self.__userTokens:
            params = {'token': token}
            data = {'tlm': self.telemetryData}
            try:
                response = self.__session.post(API_BASE_URL + 'tlm/send', params=params, json=data)
                if response.status_code != codes['ok']:
                    LOG.error(f'ABRP send telemetry for vehicle {self.weConnectVehicle.vin.value} for account {account}'
                              f' failed with status code {response.status_code}')
                else:
                    data = response.json()
                    if 'status' in data:
                        if data['status'] != 'ok':
                            LOG.error(f'ABRP send telemetry for vehicle {self.weConnectVehicle.vin.value} for account {account} failed')
                        if 'missing' in data:
                            LOG.info(f'ABRP send telemetry for vehicle {self.weConnectVehicle.vin.value} for account {account}: {data["missing"]}')
                    else:
                        LOG.error(f'ABRP send telemetry for vehicle {self.weConnectVehicle.vin.value} for account {account} returned unexpected data')
            except RequestException as e:
                LOG.error(f'ABRP send telemetry for vehicle {self.weConnectVehicle.vin.value} failed: {e}, will try again after next interval')

    def commit(self):  # noqa: C901
        if self.weConnectVehicle.statusExists('charging', 'batteryStatus'):
            batteryStatus = self.weConnectVehicle.domains['charging']['batteryStatus']
            if batteryStatus.carCapturedTimestamp.enabled and batteryStatus.carCapturedTimestamp.value is not None:
                self.telemetryData['utc'] = batteryStatus.carCapturedTimestamp.value.timestamp()
            if batteryStatus.currentSOC_pct.enabled and batteryStatus.currentSOC_pct.value is not None:
                self.telemetryData['soc'] = batteryStatus.currentSOC_pct.value
            if batteryStatus.cruisingRangeElectric_km.enabled and batteryStatus.cruisingRangeElectric_km.value is not None:
                self.telemetryData['est_battery_range'] = batteryStatus.cruisingRangeElectric_km.value

        if self.weConnectVehicle.statusExists('parking', 'parkingPosition'):
            parkingPosition = self.weConnectVehicle.domains['parking']['parkingPosition']
            if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                    and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                self.telemetryData['lat'] = parkingPosition.latitude.value
                self.telemetryData['lon'] = parkingPosition.longitude.value
        if 'lat' in self.telemetryData:
            self.telemetryData['is_parked'] = True
        else:
            self.telemetryData['is_parked'] = False

        if self.weConnectVehicle.statusExists('measurements', 'odometerStatus') \
                and self.weConnectVehicle.domains['measurements']['odometerStatus'].enabled:
            odometerMeasurement = self.weConnectVehicle.domains['measurements']['odometerStatus']
            if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                self.telemetryData['odometer'] = odometerMeasurement.odometer.value

        if self.weConnectVehicle.statusExists('charging', 'chargingStatus') \
                and self.weConnectVehicle.domains['charging']['chargingStatus'].enabled:
            chargingStatus = self.weConnectVehicle.domains['charging']['chargingStatus']
            if chargingStatus.chargingState.enabled and chargingStatus.chargingState.value in [ChargingStatus.ChargingState.CHARGING]:
                self.telemetryData['is_charging'] = True
            else:
                self.telemetryData['is_charging'] = False

            if chargingStatus.chargePower_kW.enabled and chargingStatus.chargePower_kW.value is not None:
                self.telemetryData['power'] = chargingStatus.chargePower_kW.value * -1

        self.updateTelemetry()
        self.telemetryData.clear()
