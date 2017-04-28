# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import logging

import requests
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth, OPTIONAL

from .base import Base
from .dataarchive import DataArchive
from .point import Point
from .structures import TypedList
from .value import Value

log = logging.getLogger(__name__)


class PIWebAPI(Base):
    """Provide integration with the OSIsoft PI Web PIWebAPI.
    
    TODO: document class methods.
    
    TODO: document class parameters.
    """

    def __init__(self, url='https://dev.dstcontrols.local/piwebapi/',
                 verifyssl=True, authtype='kerberos', username=None,
                 password=None):
        # type: (str, bool, str, Union[None, None, None, str], Union[None, None, None, str]) -> None


        log.info('Instantiating the OSIsoftPy PIWebAPI with the following '
                 'arguments: URL: %s, VerifySSL: %s, AuthType: %s, '
                 'Username: %s', url, verifyssl, authtype, username)

        self.url = url
        self.verifyssl = verifyssl
        self.authtype = authtype

        log.debug('Creating Requests Session object. VerifySSL: %s, '
                  'AuthType: %s', self.verifyssl, self.authtype)

        self.session = requests.Session()
        self.session.verify = verifyssl
        self.session.auth = self.get_credentials(authtype=self.authtype,
                                                 username=username,
                                                 password=password)
        # self.isconnected = self.test_connection()

        if self.test_connection():
            log.info('OSIsoftPy PIWebAPI instantiation success using %s '
                     'against %s', authtype, self.url)
            self.dataservers = TypedList(DataArchive)
        else:
            log.error(
                'OSIsoftPy PIWebAPI instantiatian failed using %s against '
                '%s', authtype, self.url, exc_info=True)

    @staticmethod
    def get_credentials(authtype, username, password):
        """

        :param authtype: 
        :param username: 
        :param password: 
        :return: 
        """
        log.debug('Creating %s authentication object for Requests...',
                  authtype)
        if authtype.lower() == 'basic':
            return HTTPBasicAuth(username, password)
        elif authtype.lower() == 'kerberos':
            return HTTPKerberosAuth(mutual_authentication=OPTIONAL)
        else:
            raise TypeError('Error: {0} is an invalid authentication type. '
                            'Valid options are Basic and Kerberos.')

    def test_connection(self):
        """

        :rtype: bool
        """
        log.debug('Testing connection to PI Web PIWebAPI...')
        r = self.session.get(self.url)
        if r.status_code == requests.codes.ok:
            log.debug('PI Web PIWebAPI connection OK, returning True')
            return True
        log.debug('PI Web PIWebAPI connection error, Returning False')
        r.raise_for_status()
        return False

    def get_data_archive_servers(self):
        """

        :return: 
        """
        log.debug('Retrieving all PI Data Archive servers from %s', self.url)
        r = self.session.get(self.url + 'dataservers')
        if r.status_code == requests.codes.ok:
            data = r.json()
            if len(data['Items']) > 0:
                log.debug('HTTP %s - Instantiating OSIsoftPy.DataArchives()',
                          r.status_code)
                servers = TypedList(validtypes=DataArchive)
                log.debug('Staging %s PI server(s) for instantiation...',
                          data['Items'].__len__().__str__())
                for i in data['Items']:
                    try:
                        log.debug('Instantiating "%s" as '
                                  'OSIsoftPy.DataArchive...', i['Name'])
                        server = DataArchive(name=i['Name'],
                                             serverversion=i['ServerVersion'],
                                             webid=i['WebId'],
                                             isconnected=i['IsConnected'],
                                             id=i['Id'])
                        servers.append(server)
                    except Exception as e:
                        log.error('Unable to retrieve server info for '
                                  '"%s"', i['Name'], exc_info=True)
                log.debug('PI Data Archive server retrieval success! %s PI '
                          'server(s) were '
                          'found and instantiated.',
                          servers.__len__().__str__())
                return servers
        r.raise_for_status()

    def get_data_archive_server(self, name):
        """

        :param name: 
        :return: 
        """
        log.debug('Getting PI Data Archive server named "%s" from %s', name,
                  self.url)
        try:
            pi_servers = self.get_data_archive_servers()
            log.debug('Searching for a PI Data Archive server named "%s"...',
                      name)
            pi_server = next((x for x in pi_servers if x.name == name), None)
            if pi_server:
                log.debug(
                    'Found a PI Data Archive named "%s" with WebID "%s" on '
                    '%s', pi_server.name, pi_server.webid, self.url)
                return pi_server
            else:
                log.error('No PI Data Archive named "%s" was found on %s',
                          name, self.url, exc_info=True)
        except Exception as e:
            log.error(
                'Exception while searching for a PI Data Archive named "%s" '
                'from %s', name, self.url, exc_info=True)

    def get_points(self, query, count=10, scope='*'):
        """

        :param query: 
        :param count: 
        :param scope: 
        :return: 
        """
        payload = {'q': query, 'count': count, 'scope': scope}
        log.debug(
            'Executing Query against PI Web PIWebAPI Indexed Search with '
            'the following parameters: Query: "%s", Count: "%s". Payload: %s',
            query, count, payload)
        r = self.session.get(self.url + 'search/query', params=payload)
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
        else:
            data = r.json()
            if len(data['Items']) > 0:
                log.debug('HTTP %s - Instantiating OSIsoftPy.Points()',
                          r.status_code)
                points = TypedList(validtypes=Point)
                log.debug('Staging %s PI point(s) for instantiation...',
                          data['Items'].__len__().__str__())
                for i in data['Items']:
                    try:
                        log.debug('Instantiating "%s" as OSIsoftPy.Point...',
                                  i['Name'])
                        point = Point()
                        point.name = i['Name']
                        if 'description' in i:
                            point.description = i['description']
                        point.uniqueid = i['UniqueID']
                        point.webid = i['WebID']
                        point.datatype = i['DataType']

                        points.append(point)
                    except Exception as e:
                        log.error('Exception while instantiating PI '
                                  'point for '
                                  '"%s". Raw JSON: %s', i['Name'], i,
                                  exc_info=True)
                log.debug('PI Point retrieval success! %s PI '
                          'point(s) were '
                          'found and instantiated.',
                          points.__len__().__str__())

                if len(data['Errors']) != 0:
                    for error in data['Errors']:
                        try:
                            log.warning('The PI Web PIWebAPI returned the '
                                        'following error while instantiating '
                                        'PI points. '
                                        'ErrorCode: {0}, Source: {1}, '
                                        'Message {2}'.format(
                                error['ErrorCode'], error['Source'],
                                error['Message']))
                        except Exception as e:
                            log.error('Exception encounted while '
                                      'instantiating '
                                      'PI points!', exc_info=True)

                return points

    def get_values(self, points, calculationtype, start=None, end=None,
                   boundary=None, maxcount=None, interval=None):
        """

        :param points: 
        :param calculationtype: 
        :param start: 
        :param end: 
        :param boundary: 
        :param maxcount: 
        :param interval: 
        :return: 
        """
        # TODO: get_values() probably shouldn't return a sequence of Points if
        # we're just providing a single Point object.
        # TODO: param to toggle between append and overwrite TypedList(Value)

        if calculationtype.lower() == 'current':
            for point in points:
                log.debug('Retrieving current value for %s...', point.name)
                endpoint = '{0}streams/{1}/value'.format(self.url, point.webid)
                r = self.session.get(endpoint)
                if r.status_code != requests.codes.ok:
                    r.raise_for_status()
                else:
                    data = r.json()
                    log.debug('HTTP %s - Instantiating OSIsoftPy.Values()',
                              r.status_code)
                    log.debug('Staging PI point value for '
                              'instantiation...')
                    try:
                        log.debug('Instantiating current value from %s for '
                                  '%s as an OSIsoftPy.Value...',
                                  data['Timestamp'], point.name)
                        value = Value(calculationtype=calculationtype.lower(),
                                      datatype=point.datatype,
                                      timestamp=data['Timestamp'],
                                      value=data['Value'],
                                      unitsabbreviation=data[
                                          'UnitsAbbreviation'],
                                      good=data['Good'],
                                      questionable=data['Questionable'],
                                      substituted=data['Substituted'])
                        point.current_value = value
                    except Exception as e:
                        log.error('Exception while instantiating current value'
                                  'from %s for %s. Raw JSON: %s',
                                  data['Timestamp'], point.name, data,
                                  exc_info=True)
                    log.debug(
                        'PI point value retrieval success! Current value '
                        'from %s for %s was found and instantiated.',
                        data['Timestamp'], point.name)

            return points