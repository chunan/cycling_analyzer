"""Credit to cast42/parse_strava_gpx_minidom.py."""
import collections
import datetime
import logging
import numpy
from xml.dom import minidom


Track = collections.namedtuple('Track', ['name', 'points'])


def ValueOrNone(v_str, dtype):
  try:
    return dtype(v_str)
  except:
    return None

def NoneToZero(value):
  return 0 if value is None else value

def GetTime(t_str):
  try:
    return datetime.datetime.strptime(t_str, '%Y-%m-%dT%H:%M:%S.%fZ')
  except ValueError:
    return datetime.datetime.strptime(t_str, '%Y-%m-%dT%H:%M:%SZ')


def CastVote(point, poll):
  for key, val in point.items():
    if val is not None:
      poll[key] += 1

def ParseTrk(trk, poll):
  name = trk.getElementsByTagName('name')[0].firstChild.data
  points = []
  for trkseg in trk.getElementsByTagName('trkseg'):
    for trkpt in trkseg.getElementsByTagName('trkpt'):
      lat = ValueOrNone(trkpt.getAttribute('lat'), float)
      lon = ValueOrNone(trkpt.getAttribute('lon'), float)
      ele = ValueOrNone(trkpt.getElementsByTagName('ele')[0].firstChild.data, float)
      dt = GetTime(trkpt.getElementsByTagName('time')[0].firstChild.data)
      extensions = trkpt.getElementsByTagName('extensions')[0]
      power = ValueOrNone(extensions.getElementsByTagName('power')[0].firstChild.data, float)
      trkPtExtension = extensions.getElementsByTagName('gpxtpx:TrackPointExtension')[0]
      hl, cad = None, None
      if trkPtExtension:
        hr = ValueOrNone(trkPtExtension.getElementsByTagName('gpxtpx:hr')[0].firstChild.data, int)
        cad = ValueOrNone(trkPtExtension.getElementsByTagName('gpxtpx:cad')[0].firstChild.data, int)
      point = {'Lat': lat, 'Long': lon, 'Ele': ele, 'Time': dt, 'Hr': hr, 'cad': cad, 'Power': power}
      CastVote(point, poll)
      points.append(point)

  return Track(name, points)


def PointsIn(tracks):
  for track in tracks:
    for point in track.points:
      yield point


def PointsToSequences(tracks, poll):
  """Conver list of points to sequences.

  Ignore keys which has too many missing values.
  """
  max_vote = max(poll.values())
  keys = []
  for key, vote in poll.items():
    if max_vote - vote < 10:
      keys.append(key)
    else:
      logging.error('Too many missing values for %s(%d < %d)', key, vote, max_vote)

  data = collections.defaultdict(list)

  for key in keys:
    for point in PointsIn(tracks):
      data[key].append(NoneToZero(point[key]))
    data[key] = numpy.asarray(data[key])
    print('data[{}](shape={})={}'.format(key, data[key].shape, data[key][:5]))
  
  return data


def ParseGpx(filename):
  doc = minidom.parse(filename)
  doc.normalize()
  gpx = doc.documentElement
  tracks = []
  poll = collections.defaultdict(int)
  for node in gpx.getElementsByTagName('trk'):
    tracks.append(ParseTrk(node, poll))

  return PointsToSequences(tracks, poll)
