#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pyaudio
import wave
import numpy

CHUNK = 1024 * 2

# 設定内容
ACTIVE = []
FILENAMES = []
SKIP = []
TITLE = []
LEN = 0


def readConf(conffile):
    global ACTIVE
    global FILENAMES
    global SKIP
    global TITLE
    global LEN

    conf = open(conffile, 'rb')
    count = 0
    for line in conf:
        if (len(line) == 0):
            continue
        if (line[0] == '#'):
            continue

# バージョン
        if (line[0] == 'v'):
            continue
# 音声
        else:
            lines = line.rstrip().split(',')
            count += 1
            TITLE.append(lines[0])
            FILENAMES.append(lines[1])
            SKIP.append(int(lines[2]))
            ACTIVE.append(1)

    LEN = count


def playSound():
    global ACTIVE
    global FILENAMES
    global SKIP
    global TITLE
    global LEN

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
    while (True):
        fin = False

# 音声合成
        for i in range(LEN):
            data = wf[i].readframes(CHUNK)
            if (data == ''):
                fin = True
                break
            data16 = numpy.frombuffer(data, dtype="int16")
            data64 = data16.astype("int64")
            if (i == 0):
                dlen = len(data)
                idata = data64
            else:
# 一ファイル終了したら全ファイル終了．
# TODO: どれか1ファイルアクティブだったら調整．
                if (dlen != len(data)):
                    fin = True
                    break
                idata += data64
        if (fin is True):
            break
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


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print "Usage %s conffile" % (sys.argv[0])
        exit(1)

    readConf(sys.argv[1])
    playSound()
