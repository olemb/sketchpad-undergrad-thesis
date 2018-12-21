"""
The recording logic.
"""

import wave
import audioop
import sched

if 1:
    import pablio
    using_pablio = 1
else:
    import ossaudio as pablio
    using_pablio = 0

def format_time(secs):
    min = int(secs / 60)
    sec = int(secs % 60)
    rem = int(secs % 1.0 * 100)
    
    return '%02d:%02d.%02d' % (min, sec, rem)

class SampleParams:
    """Attributes of this class are read-only!"""
    
    def __init__(self,
                 nchannels=2,
                 sampwidth=2,
                 framerate=44100,
                 blocksize=512):
        self.framerate = framerate
        self.nchannels = nchannels
        self.sampwidth = sampwidth
        self.blocksize = blocksize  # Frames per block

        if sampwidth == 2:
            self.minval = -(2**15)
            self.maxval = 2**15-1
            self.scale = float(2**15-1)
        elif sampwidth == 1:
            self.minval = 128
            self.maxval = -127
            self.scale = float(127)

        self._bytes_per_frame = self.sampwidth * self.nchannels
        self._bytes_per_block = self.blocksize * self._bytes_per_frame
        self._seconds_per_block = self.blocksize / float(self.framerate)

        # A block of silence
        self.silence = '\0' * self._bytes_per_block

    def pos2secs(self, pos):
        return pos * self._seconds_per_block
        
    def secs2pos(self, secs):
        return secs / self._seconds_per_block

def load_buffer(filename, params):
    # Todo: what to do if sample params of file != params?
    
    buffer = []

    file = wave.open(filename, 'r')

    while 1:
        block = file.readframes(params.blocksize)
        if block == '':
            break
        else:
            if len(block) < len(params.silence):
                print 'Padding last block (was %s,' % len(block),
                
                # Pad last block if necessary
                block += params.silence[:-len(block)]
                print 'is %d)' % len(block)
            
            buffer.append(block)

    return buffer

def save_buffer(filename, params, buffer):
    file = wave.open(filename, 'w')
    file.setframerate(params.framerate)
    file.setnchannels(params.nchannels)
    file.setsampwidth(params.sampwidth)

    for block in buffer:
        file.writeframes(block)

class Recorder:
    def __init__(self, params=None):
        self.params = params or SampleParams(framerate=44100,
                                             nchannels=2,
                                             sampwidth=2,
                                             blocksize=512)
        self.new()
        self.open_audio()
        
        sched.realtime()

    def __del__(self):
        self.close_audio()  # or is this done automatically? (Yes, probably)

    def set_pos(self, newpos=None):
        if newpos != None:
            self.pos = newpos

    def new(self):
        self.record_buffer = []
        self.undo_buffer = None

        self.stop()
        self.filename = None
        self.changes = 0

    def undo(self, pos=0):
        self.stop(pos)

        if self.undo_buffer != None:
            if self.record_buffer:
                self.changes -= 1
            self.record_buffer = self.undo_buffer
            self.undo_buffer = None

    def record(self, pos=0):
        # Make a copy of the recording
        self.undo_buffer = self.record_buffer[:]

        # If pos > end of the buffer, fill the gap with silence
        gap = pos - len(self.record_buffer)
        if gap > 0:
            silence = self.params.silence
            self.record_buffer.extend([silence] * gap)

        self.changes += 1

        self.mode = 'recording'
        self.set_pos(pos)

    def play(self, pos=0):
        # Make sure we don't play beyond the end
        pos = min(pos, len(self.record_buffer))

        self.mode = 'playing'
        self.set_pos(pos)

    def stop(self, pos=0):
        self.mode = 'stopped'
        self.set_pos(pos)

    def load(self, filename):
        self.new()
        self.record_buffer = load_buffer(filename, self.params)
        self.filename = filename

    def save(self, filename):
        save_buffer(filename, self.params, self.record_buffer)
        self.filename = filename
        self.changes = 0

    def update(self, prefunc=None, postfunc=None, monitor=0):
        # Convenient shortcuts
        silence = self.params.silence
        blocksize = self.params.blocksize
        sampwidth = self.params.sampwidth

        latency = self.audio.minlatency
        latency_correction = int(round(latency * 300))  # Magic value!

        #print 'Latency correction:',
        #print '%.1f' % ((latency_correction * blocksize) / 44100.0 * 1000),
        #print 'ms'

        input = self.audio.readframes(blocksize)

        if prefunc:
            input = prefunc(input)

        if self.mode == 'recording':
            if using_pablio:
                play_ahead = latency_correction
            else:
                play_ahead = 3

        else:
            play_ahead = 0

        # Output
        if self.mode == 'stopped':
            output = silence
        else:
            try:
                output = self.record_buffer[self.pos+play_ahead]
            except IndexError:
                output = silence

        if self.mode == 'playing':
            if self.pos < len(self.record_buffer):
                self.pos += 1
        elif self.mode == 'recording':
            if self.pos == len(self.record_buffer):
                self.record_buffer.append(input)
            else:
                old = self.record_buffer[self.pos]
                new = audioop.add(old, input, sampwidth)
                self.record_buffer[self.pos] = new
            self.pos += 1

        if postfunc:
            output = postfunc(output)

        if monitor:
            output = audioop.add(output, input, sampwidth)

        # Echo input
        self.audio.writeframes(output)

        # Leave these here in case the GUI needs them
        # (What's needed? I'll have to think about this a little more.)
        self.input = input
        self.output = output
        # self.buf = buf  # What's in the sample buffer

    def playing(self, start_pos):
        self.pos = start_pos
        

    def __len__(self):
        return len(self.record_buffer)

    def get_time(self):
        "Return current position in seconds"
        return self.params.pos2secs(self.pos)

    def get_total(self):
        "Return length of recording in seconds"
        return self.params.pos2secs(len(self.record_buffer))

    def get_undoable(self):
        return (self.undo_buffer != None)


    #
    # Audio
    #
    def open_audio(self):
        self.audio = pablio.open('r+', self.params.framerate)

    def close_audio(self):
        self.audio.close()
        del self.audio

    def pause_audio(self):
        self.close_audio()

    def resume_audio(self):
            self.open_audio()

if __name__ == '__main__':
    rec = Recorder(params)

    print 'Recording for about a second'
    rec.record()
    for i in range(100):
        rec.update()

    print 'Playing back the recording'
    rec.play()
    for i in range(100):
        rec.update()
