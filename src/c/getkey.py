import termios
import sys
import atexit
import select

"""Maybe not the most elegant way of doing it, but this is a
prototype."""

def init():
    fd = sys.stdin.fileno()
    modes = termios.tcgetattr(fd)
    savemodes = modes[:]
    modes[3] &= ~(termios.ICANON|termios.ECHO)
    termios.tcsetattr(fd, termios.TCSANOW, modes)
    atexit.register(cleanup, fd, savemodes)

def cleanup(fd, savemodes):
    termios.tcsetattr(fd, termios.TCSANOW, savemodes)

init()

def getkey(timeout):
    poller = select.poll()
    poller.register(sys.stdin.fileno(), select.POLLIN)

    fds = poller.poll(timeout)
    if fds:
        return sys.stdin.read(1)
    else:
        return 0
