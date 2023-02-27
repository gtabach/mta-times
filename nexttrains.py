# This script gets the next three trains in each direction going to the Nostrand Av and
# President St subway stops in Crown Heights, as well as any active alerts on the 2/3/4/5


from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from operator import itemgetter
import urllib.request
import time

# I wrote this bit 5 years ago and I don't remember what it does
feeds = gtfs_realtime_pb2.FeedMessage()
feeda = gtfs_realtime_pb2.FeedMessage()

url = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/'
key = '[insert yours here]'

currtime = time.time()

# Get train times
# This URL is for the IRT lines, see https://api.mta.info/#/subwayRealTimeFeeds
rs = urllib.request.Request(url+'nyct%2Fgtfs')
rs.add_header('x-api-key', key)
responses = urllib.request.urlopen(rs)
feeds.ParseFromString(responses.read())

# Get alerts
ra = urllib.request.Request(url+'camsys%2Fsubway-alerts')
ra.add_header('x-api-key', key)
responsea = urllib.request.urlopen(ra)
feeda.ParseFromString(responsea.read())

# Whatever the protobuff is
subway_feed = protobuf_to_dict(feeds)
subway_data = subway_feed['entity']

alert_feed = protobuf_to_dict(feeda)
alert_data = alert_feed['entity']

# Stop codes from stops.txt here: http://web.mta.info/developers/data/nyct/subway/google_transit.zip
# Put all trains scheduled for these stops in dict
# Dict format: stop:line:direction:times
subs = {'241': {}, '248': {}}
subdict = {'241': 'President St', '248': 'Nostrand Av'}

# For each train, pull out the relevant stops (if any) and put them into the subs dict
for train in subway_data:
    if 'trip_update' in train:
        train_trip = train['trip_update']
        for stop in train_trip['stop_time_update']:
            if stop['stop_id'] in ['241N', '241S', '248N', '248S']:
                route = train_trip['trip']['route_id']
                sid = stop['stop_id'][:-1]
                sdr = stop['stop_id'][-1]
                if route not in subs[sid]:
                    subs[sid][route] = {'N': [], 'S': []}
                subs[sid][route][sdr].append(stop['departure']['time'])

# Get the three upcoming trains in each direction and print out their scheduled arrival time (in minutes from present)
for sid in subs:
    print(subdict[sid])
    for route in subs[sid]:
        ntimes, stimes = [' '.join([str(int((x-currtime)//60)) for x in subs[sid][route][d] if currtime < x][:3]) for d in ['N', 'S']]
        print('{}: {:<9} {}'.format(route, ntimes, stimes))

# For each alert, pick out the ones on the right lines that are active and print out their header below the upcoming trains
# (No need to print out the whole detailed alert)
for alert in alert_data:
    use_alert = False
    for route in alert['alert']['informed_entity']:
        if 'route_id' in route and route['route_id'] in ['2', '3', '4', '5']:
            for times in alert['alert']['active_period']:
                if times['start'] < currtime and ('end' not in times or times['end'] > currtime):
                    use_alert = True
    if use_alert:
        for trans in alert['alert']['header_text']['translation']:
            if trans['language'] == 'en':
                print(trans['text'])