#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import wave
import numpy


CHUNK = 1024


def zeroCount(path):
    wf = wave.open(path, 'rb')

    channels = wf.getnchannels()
    head = 0
    Fin = False
    while (True):
        data = wf.readframes(CHUNK)
        if (data == ''):
            print "File Error"
            return -1
        data16 = numpy.frombuffer(data, dtype="int16")
        for i in range(len(data16)):
            if (data16[i] != 0):
                Fin = True
                break;
            head += 1
        if Fin == True:
            break
    wf.close()

    return head / channels


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print "Usage %s *.wav" % (sys.argv[0])
        exit(1)

    count = zeroCount(sys.argv[1])
    print count
