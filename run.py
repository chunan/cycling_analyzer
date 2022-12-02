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


def PlotPower(data, title):
  # Params
  N = (10,)
  StartMinute = 0.
  EndMinute = Inf
  BinWidth = 10.

  # Variables.
  power = data['Power']
  full_dur_secs = len(power)
  power_smooth_10 = numpy.convolve(power, numpy.ones((10,)) / float(10), mode='valid')
  max_power_10 = numpy.max(power_smooth_10)
  upper_range = max(BinWidth * numpy.ceil(max_power_10 / BinWidth), 400)

  # 0. Select focused region. -------------------------------------------------------
  EndMinute = min(EndMinute, full_dur_secs / 60.)
  print('Time: {:.1f}m ~ {:.1f}m'.format(StartMinute, EndMinute))
  power = power[int(StartMinute * 60) : int(EndMinute * 60 + 1)]
  time = StartMinute + numpy.arange(len(power)) / 60.
  print('power.shape={}'.format(power.shape))

  # 1. Plot power track. -------------------------------------------------------------
  power_smooth = collections.OrderedDict()
  for n in N:
    if n == 10:
      power_smooth[n] = power_smooth_10
    else:
      power_smooth[n] = numpy.convolve(power, numpy.ones((n,)) / float(n), mode='valid')
  power_cum = numpy.cumsum(power)
  #power_cumavg = power_cum / numpy.arange(1, len(power_cum) + 1)
  print('time.shape={}'.format(time.shape))

  fig = pyplot.figure(figsize=(20, 12), dpi=300)
  ax = fig.add_subplot(2, 1, 1)

  # Instant Power line.
  #ax.plot(time, power, '-', color='lightblue', linewidth=1)

  # Smoothed power lines.
  for n, s in power_smooth.items():
    ax.plot(time[n - 1:], s, '-', linewidth=1, label='{}_avg'.format(DurFormat(n)))

  # Accumulated power line.
  #ax.plot(time, power_cumavg, '-', linewidth=1, label='cum_avg')

  # Power zone colors.
  zeros = numpy.zeros_like(power_smooth_10)
  alpha = 0.2
  ax.fill_between(time[9:], zeros, power_smooth_10, where=power_smooth_10 >= 1.06 * FTP, facecolor='red', alpha=alpha)
  ax.fill_between(time[9:], zeros, power_smooth_10, where=numpy.logical_and(power_smooth_10 >= .95 * FTP, power_smooth_10 < 1.06 * FTP), facecolor='orange', alpha=alpha)
  ax.fill_between(time[9:], zeros, power_smooth_10, where=numpy.logical_and(power_smooth_10 >= .84 * FTP, power_smooth_10 < .95 * FTP), facecolor='yellow', alpha=alpha)
  ax.fill_between(time[9:], zeros, power_smooth_10, where=numpy.logical_and(power_smooth_10 >= .69 * FTP, power_smooth_10 < .84 * FTP), facecolor='green', alpha=alpha)
  ax.fill_between(time[9:], zeros, power_smooth_10, where=power_smooth_10 < .69 * FTP, facecolor='grey', alpha=alpha)

  ax.set_xticks(numpy.arange(0, time[-1] + 1, 5), minor=False)
  ax.set_yticks(numpy.arange(0, upper_range + 50, 50), minor=False)
  ax.set_ylim(0, upper_range)
  ax.set_xlim(StartMinute, EndMinute)
  ax.xaxis.grid(linestyle='-', which='major')
  ax.xaxis.grid(linestyle='--', which='minor')
  ax.yaxis.grid(linestyle='-', which='major')
  ax.yaxis.grid(linestyle='--', which='minor')
  ax.legend(loc='upper left')
  ax.set_xlabel('Time (min)')
  ax.set_ylabel('Power (W)')
  ax.tick_params(labelright=True)
  ax.set_title(title)

  # 2. Plot power distribution. -------------------------------------------------------
  nbin = int(upper_range / BinWidth)
  weights = numpy.ones_like(power) / float(len(power))
  ax = fig.add_subplot(2, 2, 3)
  hist = ax.hist(power, bins=nbin, weights=weights, range=(0, upper_range), color='grey')
  # Convert y-axis to persentage.
  vals = ax.get_yticks()
  ax.set_yticklabels(['{:,.0%}'.format(x) for x in vals])
  for i, p, x in zip(itertools.count(), hist[0], hist[1]):
    if i % 2 == 0 or p < 0.002:
      continue
    ax.annotate('{:.1f}'.format(100. * p), xy=(BinWidth / 2 + x, p + 0.005), color='grey', ha='center', va='bottom')

  ax.grid()
  ax.set_xticks(numpy.arange(0, upper_range, BinWidth), minor=True)
  ax.set_xticks(numpy.arange(0, upper_range, 50), minor=False)
  ax.set_title('Power distribution')
  ax.xaxis.grid(linestyle='-', which='major')
  ax.xaxis.grid(linestyle='--', which='minor')
  ax.set_xlim(0, min(upper_range, 550))
  ax.set_ylim(0, 0.12)
  ax.set_xlabel('Power (W)')

  # 3. Plot peak power curve. -----------------------------------------------------------
  N = numpy.arange(1, 3601)
  labels = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 1200, 1800, 3600]
  N = TruncateLarger(N, len(power))
  labels = TruncateLarger(labels, len(power))
  power_at = [numpy.max(numpy.convolve(power, numpy.ones((n,)) / float(n), mode='valid'))
              for n in N]
  ax = fig.add_subplot(2, 2, 4)
  ax.semilogx(N, power_at, '-k', linewidth=2)
  ax.set_xticks(labels)
  ax.set_xticklabels([DurFormat(n) for n in labels])
  ax.set_xlim(0.9, 4300)
  ax.set_ylim(min(power_at) - 10, max(power_at) + 10)
  for n in labels:
    p = power_at[n - 1]
    ax.annotate('{:.0f}'.format(p), xy=(n, p + 10), color='grey', ha='center', va='bottom')
  ax.set_title('Peak power curve')
  ax.grid()

  return fig


def Run():
  assert(len(sys.argv) == 3)
  in_filename = sys.argv[1]
  basename, ext = in_filename.split('.')
  if ext == 'csv':
    data = csvparse.ParseCsv(in_filename)
  elif ext == 'gpx':
    data = gpxparse.ParseGpx(in_filename)

  fig = PlotPower(data, basename)
  filename = '{}.png'.format(basename)
  if sys.argv[2] == 'save':
    with open(filename, 'wb') as f:
      fig.savefig(f)
  elif sys.argv[2] == 'plot':
    pyplot.show()
  else:
    logging.error('Unknown command %s not in {plot, save}', sys.argv[2])

if __name__ == '__main__':
  Run()
