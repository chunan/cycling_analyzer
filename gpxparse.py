"""Credit to cast42/parse_strava_gpx_minidom.py."""
import collections
import datetime
import logging
import numpy
from xml.dom import minidom


Track = collections.namedtuple('Track', ['name', 'points'])


def Identity(x):
  return x

def ValueOrNone(obj, dtype=None, get_fn=Identity):
  try:
    value = get_fn(obj)
    value = dtype(value) if dtype else value
    return value
  except Exception as e:
    logging.info('%s', e)
    return None

def NoneToZero(value):
  return 0 if value is None else value

def GetTime(obj):
  t_str = ValueOrNone(obj, get_fn=lambda x: x[0].firstChild.data)
  if t_str is None:
    return None
  try:
    return datetime.datetime.strptime(t_str, '%Y-%m-%dT%H:%M:%S.%fZ')
  except ValueError:
    return datetime.datetime.strptime(t_str, '%Y-%m-%dT%H:%M:%SZ')

def GetHrCad(extensions):
  possible_prefixes = ('gpxtpx', 'tpx1')
  hr, cad = None, None
  for prefix in possible_prefixes:
    try:
      trkPtExtension = extensions.getElementsByTagName(
          f'{prefix}::TrackPointExtension')[0]
      hr = ValueOrNone(
          trkPtExtension.getElementsByTagName('{prefix}:hr')[0].firstChild.data,
          int)
      cad = ValueOrNone(
          trkPtExtension.getElementsByTagName('{prefix}:cad')[0].firstChild.data,
          int)
    except:
      continue
    else:
      break
  return hr, cad


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
      ele = ValueOrNone(trkpt.getElementsByTagName('ele'), float,
                        lambda x: x[0].firstChild.data)
      dt = GetTime(trkpt.getElementsByTagName('time'))
      extensions = ValueOrNone(trkpt.getElementsByTagName('extensions'),
                               get_fn=lambda x: x[0])
      try:
          power = ValueOrNone(
              extensions.getElementsByTagName('power')[0].firstChild.data,
              float)
      except:
          power = 0
      hr, cad = GetHrCad(extensions)
      point = {
          'Lat': lat,
          'Long': lon,
          'Ele': ele,
          'Time': dt,
          'Hr': hr,
          'cad': cad,
          'Power': power,
      }
      CastVote(point, poll)
      points.append(point)

  return Track(name, points)


def Flatten(tracks):
  for track in tracks:
    for point in track.points:
      yield point


def PointsToSequences(tracks, poll):
  """Conver list of points to sequences.

  Ignore keys which has too many missing values.
  """
  max_vote = max(poll.values())
  good_keys = []
  for key, vote in poll.items():
    if max_vote - vote < 200:
      good_keys.append(key)
    else:
      logging.error(
          'Too many missing values for %s(%d < %d)', key, vote, max_vote)

  data = collections.defaultdict(list)

  for key in good_keys:
    for point in Flatten(tracks):
      data[key].append(NoneToZero(point[key]))
    data[key] = numpy.asarray(data[key])
    print('data[{}](shape={})={}'.format(key, data[key].shape, data[key][:5]))

  return data


def ParseGpx(filename):
  """Parse gpx file.

  Args:
    filename: the gpx filename

  Returns:
    A Dict[str, nparray] whose keys includes 'Lat', 'Long', 'Ele', 'Time', 'Hr',
    'cad', 'Power'.
  """
  doc = minidom.parse(filename)
  doc.normalize()
  gpx = doc.documentElement
  tracks = []
  poll = collections.defaultdict(int)
  # A workout can have multiple tracks, but they are flattened into a single
  # sequence in PointsToSequences.
  for node in gpx.getElementsByTagName('trk'):
    tracks.append(ParseTrk(node, poll))

  return PointsToSequences(tracks, poll)
