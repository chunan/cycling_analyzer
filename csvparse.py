import collections
import numpy


Indices = {'Lat': 3, 'Long': 4, 'Hr': 5, 'Ele': 10, 'Power': 11}


def InvalidLine(line):
  for i in Indices.values():
    if line[i] != '':
      return False
  return True


def ParseCsv(filename):
  with open(filename) as f:
    raw_data = [line.split(',') for line in f.read().split('\n') if line]

  captions = {key: raw_data[0][i] for key, i in Indices.items()}

  data = collections.defaultdict(list)

  for line in raw_data[1:]:
    if InvalidLine(line):
      continue
    for key, i in Indices.items():
      data[key].append(float(line[i]) if line[i] else 0.)

  for key, seq in data.items():
    data[key] = numpy.asarray(seq)
    print('data[{}](shape={})={}'.format(key, data[key].shape, data[key][:5]))

  return data
