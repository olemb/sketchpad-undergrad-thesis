INCLUDE=-I/usr/local/include/python2.2
CFLAGS=-O6 -Wall $(INCLUDE)
CC=gcc

all: _sched.so

_sched.so: $(OBJS) _sched.o
	$(CC) $(CFLAGS) -shared -o _sched.so $(OBJS) _sched.o

clean:
	rm -f *.o *.so *.pyc *.pyo

ps:
	a2ps \
	OVERVIEW record.py Recorder.py LayerDisplay.py \
	LevelGraph.py ossaudio.py sched.py _sched.c cmdline.py \
	-o python.ps all.ps
