import pablio
import wave
import sys
import audioop
import time
import os
import threading
import Queue

class PeakMeter:
    """Fallrate is given in units per second"""
    
    def __init__(self, fallrate=1):
        self.fallrate = fallrate
        self.peak = 0.0
        self.last_update = time.time()

    def update(self, value):
        now = time.time()
        dtime = now - self.last_update

        self.peak = self.peak - (dtime * self.fallrate)
        if self.peak < 0:
            self.peak = 0
        self.last_update = now
        
        if value > self.peak:
            self.peak = value

    def get_string(self, width):
        bars = '|' * int(round(self.peak * width))
        bars = bars[:width]
        return bars.ljust(width)

class WaveFileWriter:
    def __init__(self, filename):
        file = wave.open(filename, 'w')
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(44100)
        self.file = file

        self.queue = Queue.Queue()
        self.thread = threading.Thread(None, self.writer)
        self.thread.start()

    def _stop(self):
        self.queue.put(0)
        self.thread.join()
        self.file.close()

    def writeframes(self, frames):
        self.queue.put(frames)

    def writer(self):
        while 1:
            buf = self.queue.get()
            if buf == 0:
                break
            self.file.writeframes(buf)

    def __del__(self):
        print '('
        self._stop()
        print ')'

    def __getattr__(self, attr):
        return getattr(self.file, attr)

def maxamp(frames):
    return (audioop.max(frames, 2) / 32767.0)

def format_time(secs):
    t = secs
    
    rem = int(t % 1.0 * 100)
    sec = int(t % 60)
    t /= 60

    min = int(t % 60)
    t /= 60

    hour = int(t % 60)
    
    return '%d:%02d:%02d.%02d' % (hour, min, sec, rem)

def print_free(file, path):
    stat = os.statvfs(path)
    free = stat.f_bavail * stat.f_frsize

    bps = float(file.getnchannels() * file.getsampwidth() * file.getframerate())
    sys.stdout.write(' (%s free)' % format_time(free / bps))


def record(filename):
    audio = pablio.open('r')
    writer = WaveFileWriter(filename)
    
    peak_meter = PeakMeter()

    framerate = float(writer.getframerate())

    print 'Recording to %s (interrupt to quit)' % filename

    i = 0
    while 1:
        frames = audio.readframes(4100)
        writer.writeframes(frames)

        peak_meter.update(maxamp(frames))
        peak = peak_meter.get_string(16)
        
        secs = writer.getnframes() / framerate
        
        #sys.stdout.write('\r%s %s [%s]' % (filename,
        #                                   format_time(secs),
        #                                   peak))
        
        # print_free(file, filename)
        sys.stdout.flush()

        i = (i + 1) % 10

if not sys.argv[1:]:
    sys.exit('Usage: filerec file.wav')

try:
    record(sys.argv[1])
except KeyboardInterrupt:
    pass

