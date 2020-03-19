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


def read_screenshot():
    im = pyscreenshot.grab(bbox=(973, 347, 1224, 389))
    txt = pytesseract.image_to_string(im)
    try:
        txt = rdata.findall(txt)[0].replace(',', '.')
        return(float(txt))
    except (ValueError, IndexError):
        print("Could not convert: %s" % repr(txt))
        return(None)


if __name__ == '__main__':
    DEBUG = {
        'data': json.load(open('200318.dat')),
        'index': 0
        }

    DEBUG = False

    data = []
    rdata = re.compile(r'[0-9]+[,.][0-9]+')
    plt.ion()
    fig = plt.figure()

    pl1 = plt.subplot2grid((1,10),(0,7), colspan = 3)
    pl2 = plt.subplot2grid((1,10),(0,0), colspan = 6)

    xfmt = md.DateFormatter('%H:%M:%S')
    pl1.xaxis.set_major_formatter(xfmt)
    pl2.xaxis.set_major_formatter(xfmt)
    plt.xticks( rotation=45 )

    plt.show()
    try:
        while True:
            if DEBUG:
                time.sleep(0.1)
                try:
                    t = DEBUG['data'][DEBUG['index']][0]
                    flt = DEBUG['data'][DEBUG['index']][1]
                except IndexError:
                    time.sleep(1)
                    continue
                DEBUG['index'] += 1
            else:
                time.sleep(1)
                t = time.time()
                flt = read_screenshot()
                if flt is None:
                    continue

            print(flt)

            if not data:
                data.append((t, flt))
                continue

            if abs(flt - data[-1][1]) < 0.00001 * data[-1][1]:
                continue
            if abs(flt - data[-1][1]) > 0.5 * data[-1][1]:
                continue

            data.append((t, flt))

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

#            plt.legend()
            plt.draw()
            fig.canvas.flush_events()


    except KeyboardInterrupt:
        print("Saved data:")
        print(data)


