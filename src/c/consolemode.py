import sys

import _record
from getkey import getkey

STOPPED = 0
PLAYING = 1
RECORDING = 3

def format_time(pos, rate=44100*2):
    secs = pos / rate
    mins, secs = divmod(secs, 60)
    return '%02d:%02d' % (mins, secs)

def update_display():
    status = _record.get_status()

    pos = format_time(status['pos'])
    end = format_time(status['used_end'])
    free = format_time(status['total_end'] - status['used_end'])

    mode = ['stopped', 'playing', '-', 'recording'][status['mode']]

    flags = ''
    if monitor_input:
        flags += ' (hear input)'
    
    line = '\r%s at %s of %s [%s free] %s' % (mode, pos, end, free, flags)
    width = 70
    sys.stdout.write((line+' '*width)[:width])
    sys.stdout.flush()

filename = '/tmp/test.wav'
monitor_input = 0
done = 0

secs = 60*3
_record.init(secs)
_record.audio_start()

while not done:
    c = getkey(100)
    if c == 0:
        # Timeout
        pass
    elif c == 'q':
        done = 1
    elif c == 'b':
        _record.switch_mode(RECORDING)
    elif c == 'n':
        _record.switch_mode(PLAYING)
    elif c == ' ':
        _record.switch_mode(STOPPED)
    elif c == '\x7f':  # Backspace
        _record.undo()
    elif c == 'm':
        monitor_input = not monitor_input
        _record.set_monitor_input(monitor_input)
    else:
        print ('keypress', c)

    update_display()

print '\nSaving recording in %s ... ' % filename
_record.audio_stop()
_record.save_recording(filename)
print 'done'
_record.cleanup()
