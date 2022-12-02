import collections
import itertools
import logging
from matplotlib import pyplot
import numpy
import sys

import csvparse
import gpxparse

Inf = float('inf')
FTP = 251.


def DurFormat(s):
  return '{}s'.format(s) if s < 60 else '{:.0f}m'.format(s / 60)


def TruncateLarger(l, n):
  """Return elementes in sorted l that are no larger than n."""
  for i, x in enumerate(l):
    if x > n:
      return l[:i]
  return l


def PlotPower(workout, fig, color):
  # Variables.
  power = workout.data['Power']
  time = workout.data['Time']
  basename = workout.basename
  N = 10

  # Smoothing.
  power_smooth = numpy.convolve(power, numpy.ones((N,)) / float(N), mode='same')

  # Plot.
  ax = fig.gca()
  ax.plot(time, power_smooth, 'o-', color=color, markersize=2, linewidth=2,
          alpha=0.2, label=basename)
  ax.legend(loc='upper left')
  ax.grid(True)
  ax.set_xlabel('Time')
  ax.set_ylabel('Power (W)')
  ax.tick_params(labelright=True)
  ax.set_title(f'smooth={N}')


# `data` is a dict to nparray.
Workout = collections.namedtuple(
    'WorkoutData', ['basename', 'ext', 'data'])

def Parse(filename):
  basename, ext = filename.split('.')
  basename = basename.split('/')[-1]
  if ext == 'csv':
    data = csvparse.ParseCsv(filename)
  elif ext == 'gpx':
    data = gpxparse.ParseGpx(filename)

  return Workout(basename, ext, data)


def Run():
  colors = ('blue', 'red', 'green', 'black', 'brown')
  assert 4 <= len(sys.argv) <= len(colors)
  assert sys.argv[1] in ('save', 'plot')
  in_filenames = sys.argv[2:]
  workouts = tuple(map(Parse, in_filenames))
  fig = pyplot.figure(figsize=(20, 12), dpi=200)
  
  for workout, color in zip(workouts, colors):
    PlotPower(workout, fig, color)

  if sys.argv[1] == 'save':
    filename = '_vs_'.join([workout.basename for workout in workouts])'
    with open(filename, 'wb') as f:
      fig.savefig(f)
  elif sys.argv[1] == 'plot':
    pyplot.show()
  else:
    raise ValueError(f'Unknown arg {sys.argv[1]}')

if __name__ == '__main__':
  Run()

