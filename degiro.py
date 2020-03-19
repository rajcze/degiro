import pytesseract
import pyscreenshot
import time
import datetime
import re
import matplotlib.pyplot as plt
import matplotlib.dates as md
from scipy import stats
import numpy
import random
import json
from flask import Flask, jsonify, request
import io
import base64
import requests



RDATA = re.compile(r'[0-9]+[,.][0-9]+')
DEBUG = {
    'data': json.load(open('200318.dat')),
    'index': 0
    }

#DEBUG = False

def read_screenshot():
    im = pyscreenshot.grab(bbox=(804, 297, 1079, 354))
    txt = pytesseract.image_to_string(im)
    try:
        txt = RDATA.findall(txt)[0].replace(',', '.')
        return float(txt)
    except (ValueError, IndexError):
        print("Could not convert: %s" % repr(txt))
        return None


def init_plot():
    my_dpi = 96
    fig = plt.figure(figsize=(1800/my_dpi, 600/my_dpi), dpi=my_dpi)
    pl1 = plt.subplot2grid((1,10),(0,7), colspan = 3)
    pl2 = plt.subplot2grid((1,10),(0,0), colspan = 6)

    xfmt = md.DateFormatter('%H:%M:%S')
    pl1.xaxis.set_major_formatter(xfmt)
    pl2.xaxis.set_major_formatter(xfmt)
    plt.xticks(rotation = 45)

    return (fig, pl1, pl2)


def plot_graph(data, pl1, pl2):
    pl1.cla()
    pl2.cla()

    intervals = {'short': 5, 'mid': 15, 'long': 45, 'history_1': 30, 'history_2': 300}
    g_params = {
        'short': {'color': 'green'},
        'mid':   {'color': 'blue'},
        'long':  {'color': 'red'},
        'history_1':  {'color': 'grey', 'linestyle': 'dotted', 'marker': '+'},
        'history_2':  {'color': 'grey', 'linestyle': 'dotted', 'marker': '.'},
        }
    show = ['short', 'mid']

    for label in show:
        i = intervals[label] * -1
        dsub = data[i:]

        dx = numpy.array([i[0] for i in dsub])
        dy = numpy.array([i[1] for i in dsub])


        slope, intercept, r_value, p_value, std_err = stats.linregress(dx, dy)
        pl1.plot(dx, intercept + slope*dx, **g_params[label])

    i = intervals['history_1'] * -1
    dsub = data[i:]
    dx = numpy.array([i[0] for i in dsub])
    dy = numpy.array([i[1] for i in dsub])
    pl1.plot(dx, dy, **g_params['history_1'])


    i = intervals['history_2'] * -1
    dsub = data[i:]
    dx = [i[0] for i in dsub]
    dy = numpy.array([i[1] for i in dsub])

    dateconv = numpy.vectorize(datetime.datetime.fromtimestamp)
    date = dateconv(dx)

    pl2.plot(date, dy, **g_params['history_2'])

def update_data(data, wait=True):
    if DEBUG:
        try:
            t = DEBUG['data'][DEBUG['index']][0]
            flt = DEBUG['data'][DEBUG['index']][1]
        except IndexError:
            return None
        DEBUG['index'] += 1
    else:
        t = time.time()
        flt = read_screenshot()
        if flt is None:
            return None

    print(flt)

    if not data:
        data.append((t, flt))
        return None

    if abs(flt - data[-1][1]) < 0.00001 * data[-1][1]:
        return None
    if abs(flt - data[-1][1]) > 0.5 * data[-1][1]:
        return None

    data.append((t, flt))
    return True


def main(url=None):
    data = []
    plt.ion()
    fig, pl1, pl2 = init_plot()
    plt.show()
    if DEBUG:
        TICK_TIME = 0.1
    try:
        while True:
            if url:
                data = requests.get(url).json()
            else:
                update_data(data)
            if not data:
                continue

            plot_graph(data, pl1, pl2)
            plt.draw()
            fig.canvas.flush_events()

    except KeyboardInterrupt:
        print("Saved data:")
        print(json.dumps(data))


DATA = []
TICK_TIME = 1.0
APP = Flask(__name__)

@APP.route('/tick')
def flask_tick():
    global TICK_TIME
    try:
        TICK_TIME = float(request.args.get('s'))
        return jsonify({'tick': TICK_TIME})
    except (ValueError, TypeError):
        return jsonify({'old_tick': TICK_TIME})

@APP.route('/data_live')
def flask_data_live():
    time.sleep(TICK_TIME)
    update_data(DATA)
    return jsonify(DATA)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'server':
            APP.debug = True
            APP.run(host='0.0.0.0')
        if sys.argv[1] == 'client':
            main(url=sys.argv[2])
    else:
        main()
