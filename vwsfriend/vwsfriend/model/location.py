import json

from sqlalchemy import Column, BigInteger, String, Float

from vwsfriend.model.base import Base


class Location(Base):
    __tablename__ = 'locations'
    osm_id = Column(BigInteger, primary_key=True)
    osm_type = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    display_name = Column(String)
    name = Column(String)
    amenity = Column(String)
    house_number = Column(String)
    road = Column(String)
    neighbourhood = Column(String)
    city = Column(String)
    postcode = Column(String)
    county = Column(String)
    country = Column(String)
    state = Column(String)
    state_district = Column(String)
    raw = Column(String)

    def __init__(self, jsonDict=None):  # noqa: C901
        if jsonDict is not None:
            if 'osm_id' in jsonDict and jsonDict['osm_id'] is not None:
                self.osm_id = int(jsonDict['osm_id'])

            if 'osm_type' in jsonDict and jsonDict['osm_type'] is not None:
                self.osm_type = jsonDict['osm_type']

            if 'lat' in jsonDict and jsonDict['lat'] is not None:
                self.latitude = jsonDict['lat']

            if 'lon' in jsonDict and jsonDict['lon'] is not None:
                self.longitude = jsonDict['lon']

            if 'display_name' in jsonDict and jsonDict['display_name'] is not None:
                self.display_name = jsonDict['display_name']

            if 'address' in jsonDict and jsonDict['address'] is not None:
                address = jsonDict['address']

                if 'amenity' in address and address['amenity'] is not None:
                    self.amenity = address['amenity']

                for attribute in ['house_number', 'street_number']:
                    if attribute in address and address[attribute] is not None:
                        self.house_number = address[attribute]
                        break

                for attribute in ['road', 'footway', 'street', 'street_name', 'residential', 'path', 'pedestrian', 'road_reference', 'road_reference_intl',
                                  'square', 'place']:
                    if attribute in address and address[attribute] is not None:
                        self.road = address[attribute]
                        break

                for attribute in ['neighbourhood', 'suburb', 'city_district', 'district', 'quarter', 'borough', 'city_block', 'residential', 'commercial',
                                  'industrial', 'houses', 'subdistrict', 'subdivision', 'ward']:
                    if attribute in address and address[attribute] is not None:
                        self.neighbourhood = address[attribute]
                        break

                for attribute in ['city', 'town', 'township']:
                    if attribute in address and address[attribute] is not None:
                        self.city = address[attribute]
                        break

                for attribute in ['postcode', 'partial_postcode']:
                    if attribute in address and address[attribute] is not None:
                        self.postcode = address[attribute]
                        break

                for attribute in ['county', 'county_code', 'department']:
                    if attribute in address and address[attribute] is not None:
                        self.county = address[attribute]
                        break

                for attribute in ['country', 'country_name']:
                    if attribute in address and address[attribute] is not None:
                        self.country = address[attribute]
                        break

                for attribute in ['state', 'province', 'state_code']:
                    if attribute in address and address[attribute] is not None:
                        self.state = address[attribute]
                        break

            if 'state_district' in jsonDict and jsonDict['state_district'] is not None:
                self.state_district = jsonDict['state_district']

            if 'namedetails' in jsonDict and jsonDict['namedetails'] is not None:
                namedetails = jsonDict['namedetails']
                for attribute in ['name', 'alt_name']:
                    if attribute in namedetails and namedetails[attribute] is not None:
                        self.name = namedetails[attribute]
                        break

            self.raw = json.dumps(jsonDict)

    def __str__(self):  # noqa: C901
        returnString = f'OSM ID: {self.osm_id}'
        if self.osm_type is not None:
            returnString += f'\nOSM Type: {self.osm_type}'
        if self.latitude is not None:
            returnString += f'\nLatitude: {self.latitude}'
        if self.longitude is not None:
            returnString += f'\nLongitude: {self.longitude}'
        if self.name is not None:
            returnString += f'\nName: {self.name}'
        if self.display_name is not None:
            returnString += f'\nDisplayName: {self.display_name}'
        if self.amenity is not None:
            returnString += f'\nAmenity: {self.amenity}'
        if self.road is not None:
            returnString += f'\nRoad: {self.road}'
        if self.house_number is not None:
            returnString += f'\nHouse Number: {self.house_number}'
        if self.neighbourhood is not None:
            returnString += f'\nNighbourhood: {self.neighbourhood}'
        if self.city is not None:
            returnString += f'\nCity: {self.city}'
        if self.postcode is not None:
            returnString += f'\nPostcode: {self.postcode}'
        if self.county is not None:
            returnString += f'\nCounty: {self.county}'
        if self.country is not None:
            returnString += f'\nCountry: {self.country}'
        if self.state is not None:
            returnString += f'\nState: {self.state}'
        if self.state_district is not None:
            returnString += f'\nState District: {self.state_district}'
        return returnString

    def displayString(self):  # noqa: C901
        if self.display_name is not None:
            returnString = self.display_name
        else:
            returnString = ''
            if self.name is not None:
                returnString += f'{self.name}, '
            if self.amenity is not None:
                returnString += f'{self.amenity}, '
            if self.road is not None:
                returnString += f'{self.road}, '
            if self.house_number is not None:
                returnString += f'{self.house_number}, '
            if self.neighbourhood is not None:
                returnString += f'{self.neighbourhood}, '
            if self.city is not None:
                returnString += f'{self.city}, '
            if self.postcode is not None:
                returnString += f'{self.postcode}, '
            if self.county is not None:
                returnString += f'{self.county}, '
            if self.country is not None:
                returnString += f'{self.country}, '
            if self.state is not None:
                returnString += f'{self.state}, '
        return returnString
