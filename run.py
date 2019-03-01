import pdb
import collections
import numpy
import sys
from matplotlib import pyplot

Indices = {'Lat': 3, 'Long': 4, 'Hr': 5, 'Ele': 10, 'Power': 11}
Inf = float('inf')


def InvalidLine(line):
  for i in Indices.values():
    if line[i] != '':
      return False
  return True


def DurFormat(s):
  return '{}s'.format(s) if s < 60 else '{}m'.format(s / 60)


def PlotPower(data, title):
  # Params
  N = (5,)
  StartMin = 0
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
  ax.plot((time[0], time[-1]), 200. * numpy.ones([2]), color='yellow', linewidth=3)
  ax.plot((time[0], time[-1]), 300. * numpy.ones([2]), color='yellow', linewidth=3)
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
  ax.set_xlabel('Power (W)')
  
  # 3. Plot peak power curve. -----------------------------------------------------------
  N = [1, 5, 10, 15, 30, 45, 60, 120, 300, 600, 900, 1200, 1800]
  for i, n in enumerate(N):
    if len(power) < n:
      N = N[:i]
      break
  power_at = [numpy.max(numpy.convolve(power, numpy.ones((n,)) / float(n), mode='valid'))
              for n in N]
  ax = fig.add_subplot(2, 2, 4)
  ax.semilogx(N, power_at, 'o-k')
  ax.set_xticks(N)
  ax.set_xticklabels([DurFormat(n) for n in N])
  ax.set_xlim(0.9, N[-1] * 1.1)
  ax.set_ylim(0, upper_range + 40)
  for n, p in zip(N, power_at):
    ax.annotate('{:.0f}'.format(p), xy=(n, p + 10), color='grey', ha='center', va='bottom')
  ax.set_title('Peak power curve')
  ax.grid()

  return fig


def PlotLoc(data):
  lat = data['Lat']
  lon = data['Long']
  fig = pyplot.figure(tight_layout=True)
  ax = fig.add_subplot(1, 1, 1)
  ax.plot(lon, lat, '-k')
  ax.axis('equal')
  ax.grid()


def Run():
  assert(len(sys.argv) == 2)
  
  with open(sys.argv[1]) as f:
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

  basename = sys.argv[1].split('.')[0]
  fig = PlotPower(data, basename)
  filename = '{}.png'.format(basename)
  with open(filename, 'w') as f:
    fig.savefig(f)
  #pyplot.show()
  

if __name__ == '__main__':
  Run()
