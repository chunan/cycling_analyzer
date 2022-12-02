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
  assert len(sys.argv) == 4
  assert sys.argv[3] in ('save', 'plot')
  in_filenames = sys.argv[1:-1]
  workouts = tuple(map(Parse, in_filenames))
  fig = pyplot.figure(figsize=(25, 15), dpi=100)
  colors = ('blue', 'red')
  for workout, color in zip(workouts, colors):
    PlotPower(workout, fig, color)

  if sys.argv[-1] == 'save':
    filename = f'{workouts[0].basename}_vs_{workout[1].basename}.png'
    with open(filename, 'wb') as f:
      fig.savefig(f)
  elif sys.argv[-1] == 'plot':
    pyplot.show()
  else:
    raise ValueError(f'Unknown arg {sys.argv[2]}')

if __name__ == '__main__':
  Run()

