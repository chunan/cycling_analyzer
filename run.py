import collections
import logging
from matplotlib import pyplot
import numpy
import sys

import csvparse
import gpxparse

Inf = float('inf')


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
  N = (5,)
  StartMin = 0.
  EndMin = Inf
  BinWidth = 10.

  # Variables.
  power = data['Power']
  full_dur_secs = len(power)
  max_power = numpy.max(power)
  upper_range = BinWidth * numpy.ceil(max_power / BinWidth)

  # 0. Select focused region. -------------------------------------------------------
  EndMin = min(EndMin, full_dur_secs / 60.)
  print('Time: {:.1f}m ~ {:.1f}m'.format(StartMin, EndMin))
  power = power[int(StartMin * 60) : int(EndMin * 60 + 1)]
  time = StartMin + numpy.arange(len(power)) / 60.
  print('power.shape={}'.format(power.shape))

  # 1. Plot power track. -------------------------------------------------------------
  power_smooth = collections.OrderedDict()
  for n in N:
    power_smooth[n] = numpy.convolve(power, numpy.ones((n,)) / float(n), mode='valid')
  power_cum = numpy.cumsum(power)
  power_cumavg = power_cum / numpy.arange(1, len(power_cum) + 1)
  print('time.shape={}'.format(time.shape))
  
  fig = pyplot.figure(figsize=(20, 12), dpi=200, tight_layout=True)
  ax = fig.add_subplot(2, 1, 1)
  ax.plot((time[0], time[-1]), 238. * numpy.ones([2]), color='yellow', linewidth=3)
  ax.plot(time, power, '-', color='grey', linewidth=1)
  for n, s in power_smooth.items():
    ax.plot(time[n - 1:], s, '-', linewidth=2, label='{}_avg'.format(DurFormat(n)))
  ax.plot(time, power_cumavg, '-', linewidth=3, label='cum_avg')
  ax.set_xticks(numpy.arange(0, time[-1] + 1, 5), minor=False)
  ax.set_xticks(numpy.arange(0, time[-1] + 1), minor=True)
  ax.set_yticks(numpy.arange(0, upper_range + 50, 50), minor=False)
  ax.set_yticks(numpy.arange(0, upper_range + 10, 10), minor=True)
  ax.set_ylim(0, upper_range)
  ax.set_xlim(StartMin, EndMin)
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
  for p, x in zip(hist[0], hist[1]):
    if p < 0.002:
      continue
    ax.annotate('{:.1f}'.format(100. * p), xy=(BinWidth / 2 + x, p + 0.005), color='grey', ha='center', va='bottom')

  ax.grid()
  ax.set_xticks(numpy.arange(0, upper_range, BinWidth), minor=True)
  ax.set_xticks(numpy.arange(0, upper_range, 50), minor=False)
  ax.set_title('Power distribution')
  ax.xaxis.grid(linestyle='-', which='major')
  ax.xaxis.grid(linestyle='--', which='minor')
  ax.set_xlim(0, 400)
  ax.set_ylim(0, 0.12)
  ax.set_xlabel('Power (W)')
  
  # 3. Plot peak power curve. -----------------------------------------------------------
  N = numpy.arange(1, 3601)
  labels = [1, 5, 10, 15, 30, 45, 60, 120, 300, 600, 900, 1200, 1800, 2400, 3000, 3600]
  N = TruncateLarger(N, len(power))
  labels = TruncateLarger(labels, len(power))
  power_at = [numpy.max(numpy.convolve(power, numpy.ones((n,)) / float(n), mode='valid'))
              for n in N]
  ax = fig.add_subplot(2, 2, 4)
  ax.semilogx(N, power_at, '-k')
  ax.set_xticks(labels)
  ax.set_xticklabels([DurFormat(n) for n in labels])
  ax.set_xlim(0.9, 4300)
  ax.set_ylim(0, 1100)
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
