"""
Scraping some BOM data
"""
import datetime
import pytz
import ciso8601
from types import SimpleNamespace
import requests
import lxml
import lxml.etree

__all__ = (
    'get_stations',
    'get_station_data',
    'mk_station_selector',
)




def get_stations(time=None,
                 observation='http://bom.gov.au/waterdata/services/parameters/Storage Level',
                 url='http://www.bom.gov.au/waterdata/services'):
    """ Get list of stations

        :param time: tuple of datetime.datetime objects, or None to query from 1980-1-1 to Now

        Returns
        ========
        List of stations:
         .name -- string, human readable station name
         .pos  -- Coordinate of the station or None
         .url  -- service url identifier
    """

    data = tpl_get_stations.format(observation=observation,
                                   **_fmt_time(time))
    rr = requests.post(url, data=data)

    return _parse_station_data(rr.text)



def _parse_station_data(text):
    def parse_pos(pos):
        if pos is None:
            return None
        return tuple(_parse_float(x)
                     for x in pos.split(' '))

    root = lxml.etree.fromstring(text)

    data = [[e.text for e in root.findall('.//{http://www.opengis.net/gml/3.2}' + t)]
            for t in ['name', 'identifier', 'pos']]

    return [SimpleNamespace(name=name, iden=identifier, pos=parse_pos(pos))
            for name, identifier, pos in zip(*data)]

def _fmt_time(time=None):
    if time is None:
        time = (datetime.datetime(1900, 1, 1),
                datetime.datetime.now())

    t_start, t_end = (t.isoformat() for t in time)
    return dict(t_start=t_start, t_end=t_end)

def _parse_float(x):
    if x is None:
        return float('nan')
    try:
        return float(x)
    except ValueError:
        return float('nan')

def _parse_time(x):
    t = ciso8601.parse_datetime(x).astimezone(pytz.utc)
    return t.replace(tzinfo=None)


tpl_get_stations = '''
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"
  xmlns:sos="http://www.opengis.net/sos/2.0"
  xmlns:wsa="http://www.w3.org/2005/08/addressing"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:ows="http://www.opengis.net/ows/1.1"
  xmlns:fes="http://www.opengis.net/fes/2.0"
  xmlns:gml="http://www.opengis.net/gml/3.2"
  xmlns:swes="http://www.opengis.net/swes/2.0"
  xsi:schemaLocation="http://www.w3.org/2003/05/soap-envelope http://www.w3.org/2003/05/soap-envelope/soap-envelope.xsd http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sos.xsd"
>
    <soap12:Header>
        <wsa:To>http://www.ogc.org/SOS</wsa:To>
        <wsa:Action>http://www.opengis.net/def/serviceOperation/sos/foiRetrieval/2.0/GetFeatureOfInterest</wsa:Action>
        <wsa:ReplyTo>
            <wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsa:MessageID>0</wsa:MessageID>
    </soap12:Header>
    <soap12:Body>
        <sos:GetFeatureOfInterest service="SOS" version="2.0.0">
            <sos:observedProperty>{observation}</sos:observedProperty>
            <sos:temporalFilter>
                <fes:During>
                    <fes:ValueReference>om:phenomenonTime</fes:ValueReference>
                    <gml:TimePeriod gml:id="tp1">
                        <gml:beginPosition>{t_start}</gml:beginPosition>
                        <gml:endPosition>{t_end}</gml:endPosition>
                    </gml:TimePeriod>
                </fes:During>
            </sos:temporalFilter>
        </sos:GetFeatureOfInterest>
    </soap12:Body>
</soap12:Envelope>
'''
