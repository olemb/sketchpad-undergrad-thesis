import fcntl
import os
import struct
import array
import sys

import termios
import atexit
import select

import audioop
import wave

# ioctl operations
SNDCTL_DSP_SETDUPLEX = 0x5016
SNDCTL_DSP_SETFRAGMENT = 0xc004500a
SNDCTL_DSP_STEREO = 0xc0045003
AFMT_S16_NE = 0x10
AFMT_U8 = 0x8
AFMT_S8 = 0x40
SNDCTL_DSP_SAMPLESIZE = 0xc0045005
SNDCTL_DSP_SPEED = 0xc0045002
SNDCTL_DSP_GETBLKSIZE = 0xc0045004
SNDCTL_DSP_RESET = 0x5000
SNDCTL_DSP_POST = 0x5008

SNDCTL_DSP_GETISPACE = 0x8010500d
SNDCTL_DSP_GETOSPACE = 0x8010500c

class OSSAudioStream:
    def ioctl(self, op, arg, err):
        arg = struct.pack('i', arg)
        ret = fcntl.ioctl(self.fd, op, arg)
        return struct.unpack('i', ret)[0]

    def __init__(self):
        #self.dev = open('/dev/dsp', 'r+')
        #self.fd = self.dev.fileno()
        self.fd = os.open('/dev/dsp', os.O_RDWR)

        # Check DSP_CAP_DUPLEX
        self.ioctl(SNDCTL_DSP_SETDUPLEX, 1, 'duplex')
        self.ioctl(SNDCTL_DSP_SETFRAGMENT, 0x0002000b, 'fragment')
        self.ioctl(SNDCTL_DSP_STEREO, 1, 'stereo')
        self.ioctl(SNDCTL_DSP_SAMPLESIZE, AFMT_S16_NE, 'size')
        self.ioctl(SNDCTL_DSP_SPEED, 44100, 'rate')

        self.blocksize = self.ioctl(SNDCTL_DSP_GETBLKSIZE, 0, 'blocksize')
        self.minlatency = 0.023
        #self.minlatency = 0
        
        # Fill output buffer
        self.writeframes('\0'*2048)
        self.writeframes('\0'*2048)

    def close(self):
        os.close(self.fd)

    def pause(self):
        fcntl.ioctl(self.fd, SNDCTL_DSP_POST)

    def resume(self):
        pass

    def readframes(self, n):
        return os.read(self.fd, 2048)

    def writeframes(self, block):
        #if self.getospace() == 0:
        #    pass #print 'Output queue full'
        
        os.write(self.fd, block)

def open(*args):
    return OSSAudioStream()
