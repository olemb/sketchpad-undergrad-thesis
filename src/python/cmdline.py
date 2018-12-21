#
# Command line version of the recorder (for single user mode)
#

import sys
import termios
import atexit
import select
import time
import audioop
import freeverb

import Recorder

class Keyboard:
    def __init__(self):
        self.fd = sys.stdin
        self.raw_mode()
        self.poller = select.poll()
        self.poller.register(self.fd.fileno(), select.POLLIN)
        
    def raw_mode(self):
        modes = termios.tcgetattr(self.fd)
        self.savemodes = modes[:]
        modes[3] &= ~(termios.ICANON|termios.ECHO)
        termios.tcsetattr(self.fd, termios.TCSANOW, modes)
        atexit.register(self.reset)

    def reset(self):
        termios.tcsetattr(self.fd, termios.TCSANOW, self.savemodes)

    def getkey(self, timeout=None):
        fds = self.poller.poll(timeout)
        if fds:
            return self.fd.read(1)
        else:
            return None

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
        # Note: the value is rounded, not truncated.
        bars = '|' * int(round(self.peak * width))
        bars = bars[:width]
        return bars.ljust(width)

def make_filename():
    return time.strftime('%Y%m%d-%H%M%S.wav')
    
class Program:
    def __init__(self, loadfile=None):
        self.rec = Recorder.Recorder()
        self.keyboard = Keyboard()
        self.done = 0
        self.last_display = None
        self.peak_meter = PeakMeter()
        self.last_update = 0

        if loadfile:
            print 'Loading', loadfile
            self.rec.load(loadfile)

    def check_keys(self):
        key = self.keyboard.getkey(0)
        if not key:
            return

        if key == 'q':
            self.done = 1
        elif key == 's':
            print 'Save!'
        elif key == 'p':
            self.rec.play()
        elif key == 'r':
            self.rec.record()
        elif key == ' ':
            self.rec.stop()
        elif key == 'C':
            self.rec.new()
        elif key == chr(127):  # Backspace
            self.rec.undo()
        #else:
        #    print ord(key)

    def update(self):
        now = time.time()
        if now - self.last_update < 0.03:
            # Not time for a redraw yet
            return
        self.last_update = now
        
        peak = self.peak_meter.get_string(30)
        mode = self.rec.mode.ljust(len('recording'))

        if self.rec.get_undoable():
            undo = '(undo)'
        else:
            undo = '      '

        text = '\r  %s at %s of %s %s  [%s]' % (
            mode,
            Recorder.format_time(self.rec.get_time()),
            Recorder.format_time(self.rec.get_total()),
            undo,
            peak,
            )
	# Nah!
        if len(self.rec.record_buffer):
            undo = '*'
        else:
            undo = ' '
        if self.rec.get_undoable():
            undo += '+'
        else:
            undo += ' '
	text = '\r[%s] %s %s ' % (peak, undo, mode) 

        if text != self.last_display:
            sys.stdout.write(text)
            sys.stdout.flush()
            self.last_display = text

    def update_peak_meter(self):
        w = self.rec.params.sampwidth
        block = audioop.add(self.rec.output, self.rec.input, w)
        maxval = audioop.max(block, w)
        self.peak_meter.update(maxval/self.rec.params.scale)

    def mainloop(self):
        reverb = freeverb.reverb(roomsize=0.9, damp=1.0, dry=1.0, wet=0.1)
        
        while not self.done:
            self.check_keys()
            #self.rec.update(prefunc=reverb.process, monitor=1)
	    self.rec.update()
            self.update_peak_meter()
            self.update()
        if self.rec.get_total() > 0:
            self.rec.save(make_filename())
	print

if sys.argv[1:]:
    loadfile = sys.argv[1]
else:
    loadfile = None

p = Program(loadfile)
p.mainloop()
