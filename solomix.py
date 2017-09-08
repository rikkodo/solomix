#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pyaudio
import wave
import numpy
import threading
import readchar

CHUNK = 1024 * 2
MAX_CHANNEL = 10

MIX_FIXED = 0
MIX_LINER = 1
MIX_SQRT = 2

# 設定内容
ACTIVE = []
FILENAMES = []
SKIP = []
TITLE = []
LEN = 0
ALLFIN = False
MIX = MIX_SQRT


def readConf(conffile):
    global ACTIVE
    global FILENAMES
    global SKIP
    global TITLE
    global LEN
    global MIX

    conf = open(conffile, 'rb')
    count = 0
    for line in conf:
        if (len(line) == 0):
            continue
        if (line[0] == '#'):
            continue

        lines = line.rstrip().split(',')

        if (lines[0] == 'verison'):
            # バージョン
            continue
        elif (lines[0] == 'song'):
            # 音声
            count += 1
            TITLE.append(lines[1])
            FILENAMES.append(lines[2])
            SKIP.append(int(lines[3]))
            ACTIVE.append(1)
            print "[%d] %s" % (count % MAX_CHANNEL, lines[1])
        elif (lines[0] == 'mix'):
            if (lines[1] == 'fix'):
                MIX = MIX_FIXED
            elif (lines[1] == 'liner'):
                MIX = MIX_LINER
            elif (lines[1] == 'sqrt'):
                MIX = MIX_SQRT
        else:
            continue

    LEN = count
    if (count > MAX_CHANNEL):
        print "Too many sound."
        exit(1)


def playSound():
    global ACTIVE
    global FILENAMES
    global SKIP
    global TITLE
    global LEN
    global ALLFIN
    global MIX

    wf = []
    smpwidth = 0
    channels = 0
    framerate = 0

    # 楽曲ファイルオープン
    for i in range(LEN):
        wf.append(wave.open(FILENAMES[i], 'rb'))
        wf[i].readframes(SKIP[i])
        # フォーマットチェック
        if (i == 0):
            smpwidth = wf[0].getsampwidth()
            channels = wf[0].getnchannels()
            framerate = wf[0].getframerate()
        else:
            if ((smpwidth != wf[i].getsampwidth()) or
                    (channels != wf[i].getnchannels()) or
                    (framerate != wf[i].getframerate())):
                print >> sys.stderr, "Format not match %d." % (i)
                exit(1)

    # 出力ストリーム作成
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(smpwidth),
                    channels=channels,
                    rate=framerate,
                    output=True)

    # 楽曲再生
    while ALLFIN is False:
        fin = False

        # 音声合成
        act = ACTIVE[:]  # 配列全コピー
        actSum = sum(act)
        for i in range(LEN):
            data = wf[i].readframes(CHUNK)
            if (data == ''):
                fin = True
                break
            data16 = numpy.frombuffer(data, dtype="int16")
            data64 = data16.astype("int64") * act[i]
            if (i == 0):
                dlen = len(data)
                idata = data64
            else:
                # 一ファイル終了したら全ファイル終了．
                # TODO: どれか1ファイルでもアクティブだったら調整．
                if (dlen != len(data)):
                    fin = True
                    break
                idata += data64
        if (fin is True):
            break
        if (MIX == MIX_LINER):
            if (actSum != 0):
                idata = idata / actSum
        elif (MIX == MIX_SQRT):
            if (actSum != 0):
                if (actSum == LEN):
                    idata = idata / LEN
                else:
                    idata = idata / (numpy.sqrt(actSum) * numpy.sqrt(LEN))
        elif (MIX == MIX_FIXED):
            idata = idata / LEN
        else:  # DEFAULT
            idata = idata / LEN
        idata = idata.astype("int16")
        bdata = idata.tobytes()
        stream.write(bdata)

    # 終了処理
    for i in range(LEN):
        wf[i].close()

    stream.stop_stream()
    stream.close()

    p.terminate()

    ALLFIN = True


def keyCheck():
    global ACTIVE
    global ALLFIN
    global LEN
    soloFlag = False

    print "\n"

    while ALLFIN is False:
        for i in range(LEN):
            if (ACTIVE[i] == 1):
                print "[%d] " % ((i + 1) % MAX_CHANNEL),
            else:
                print "[ ] ",
        if (soloFlag is True):
            print "Solo",
        else:
            print "    ",
        print "\r",

        key = readchar.readchar()
        key = ord(key)
        if (ord('0') <= key and key < MAX_CHANNEL + ord('0')):
            if (key == ord('0')):
                cnt = MAX_CHANNEL
            else:
                cnt = key - ord('0')
            if (cnt <= LEN):
                if (soloFlag is True):
                    for i in range(LEN):
                        ACTIVE[i] = 0
                ACTIVE[cnt - 1] = 1 - ACTIVE[cnt - 1]

        elif (key == ord('a')):
            for i in range(LEN):
                ACTIVE[i] = 1

        elif (key == ord('r')):
            for i in range(LEN):
                ACTIVE[i] = 1 - ACTIVE[i]

        elif (key == ord('s')):
            soloFlag = not soloFlag

        elif (key == ord('q')):
            print "\nQuit."
            ALLFIN = True


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print "Usage %s conffile" % (sys.argv[0])
        exit(1)

    readConf(sys.argv[1])

    soundThread = threading.Thread(target=playSound)
    keyThread = threading.Thread(target=keyCheck)
    soundThread.start()
    keyThread.start()
    soundThread.join()
    keyThread.join()
    print ""
