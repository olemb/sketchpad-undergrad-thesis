OBJS=audio.o getkey.o lock.o record.o wave.o
INCLUDE=-I/usr/local/include/python2.2
#INCLUDE=-I/store/include/python2.1
CC=gcc

CFLAGS=-O6 -Wall $(INCLUDE)

all: record _record.so

record: $(OBJS) main.o
	$(CC) $(CFLAGS) -o record $(OBJS) main.o -lpthread

_record.so: $(OBJS) _record.o
	$(CC) $(CFLAGS) -shared -o _record.so $(OBJS) _record.o -lpthread

run:
	python record.py

clean:
	rm -f *.o

depend:
	python makedepend.py >deps

distclean: clean
	rm -f *.so record

ifeq (deps,$(wildcard deps))
include deps 
endif

ps:
	a2ps OVERVIEW \
	record.py _record.c record.h \
	record.c audio.h audio.c wave.h \
	wave.c lock.h lock.c getkey.h getkey.c main.c \
	-o c.ps
