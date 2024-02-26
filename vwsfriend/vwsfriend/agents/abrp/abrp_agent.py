import logging
import json
from requests import Session, codes
from requests.structures import CaseInsensitiveDict
from requests.adapters import HTTPAdapter, Retry
from requests import RequestException

from weconnect.elements.vehicle import Vehicle
from weconnect.elements.charging_status import ChargingStatus
from weconnect.util import kelvinToCelsius

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
        retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.__session.mount('https://api.iternio.com', HTTPAdapter(max_retries=retries))
        self.__userTokens: list[tuple[str, str]] = []
        self.subsequentErrors = 0

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

    def updateTelemetry(self):  # noqa: C901
        for account, token in self.__userTokens:
            params = {'token': token}
            data = {'tlm': self.telemetryData}
            try:
                response = self.__session.post(API_BASE_URL + 'tlm/send', params=params, json=data)
                if response.status_code != codes['ok']:
                    LOG.error(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} for account {account}'
                              f' failed with status code {response.status_code}')
                else:
                    data = response.json()
                    if data is not None:
                        if 'status' in data:
                            if data['status'] != 'ok':
                                if self.subsequentErrors > 0:
                                    LOG.error(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} for account'
                                              f' {account} failed')
                                else:
                                    LOG.warning(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} for'
                                                f' account {account} failed')
                            else:
                                self.subsequentErrors = 0
                            if 'missing' in data:
                                LOG.info(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} for account'
                                         f' {account}: {data["missing"]}')
                        else:
                            LOG.error(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} for account'
                                      f' {account} returned unexpected data')
                    else:
                        LOG.error(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} for account'
                                  f' {account} returned empty data')
            except RequestException as e:
                if self.subsequentErrors > 0:
                    LOG.error(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} failed: {e}, will try again after'
                              ' next interval')
                else:
                    LOG.warning(f'ABRP send telemetry {str(self.telemetryData)} for vehicle {self.weConnectVehicle.vin.value} failed: {e}, will try again'
                                ' after next interval')

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

        if self.weConnectVehicle.statusExists('measurements', 'temperatureBatteryStatus') \
                and self.weConnectVehicle.domains['measurements']['temperatureBatteryStatus'].enabled:
            temperatureBatteryStatus = self.weConnectVehicle.domains['measurements']['temperatureBatteryStatus']
            if temperatureBatteryStatus.temperatureHvBatteryMin_K.enabled and odometerMeasurement.temperatureHvBatteryMin_K is not None \
                    and temperatureBatteryStatus.temperatureHvBatteryMax_K.enabled and odometerMeasurement.temperatureHvBatteryMax_K is not None:
                self.telemetryData['batt_temp'] = (kelvinToCelsius(odometerMeasurement.temperatureHvBatteryMin_K.value)
                                                   + kelvinToCelsius(odometerMeasurement.temperatureHvBatteryMax_K.value)) / 2

        if self.weConnectVehicle.statusExists('charging', 'chargingStatus') \
                and self.weConnectVehicle.domains['charging']['chargingStatus'].enabled:
            chargingStatus = self.weConnectVehicle.domains['charging']['chargingStatus']
            if chargingStatus.chargingState.enabled and chargingStatus.chargingState.value in \
                [ChargingStatus.ChargingState.CHARGING,
                 ChargingStatus.ChargingState.CONSERVATION,
                 ChargingStatus.ChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION]:
                self.telemetryData['is_charging'] = True
            else:
                self.telemetryData['is_charging'] = False

            if chargingStatus.chargePower_kW.enabled and chargingStatus.chargePower_kW.value is not None:
                self.telemetryData['power'] = chargingStatus.chargePower_kW.value * -1

            if chargingStatus.chargeType.enabled and chargingStatus.chargeType.value in [ChargingStatus.ChargeType.DC]:
                self.telemetryData['is_dcfc'] = True

        self.updateTelemetry()
        self.telemetryData.clear()
