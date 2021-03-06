A Musician Friendly Multilayered Music Recording System
=======================================================

Ole Martin Bjørndalen

Department of Computer Science

University of Tromsø

Advisor: Otto J. Anshus

December 9, 2002


Abstract
--------

This report presents a simple sketchpad for layered recording of music. Mu-
sicians often need to record or try out ideas, but existing systems can be too
complex. The system was implemented at user level in C and Python and
tested on Linux and Windows XP. The recording is kept in RAM during a ses-
sion. Audio I/O latencies below 6ms were achieved by applying paches to the
Linux kernel and by compensating for expected latency. A simple user interface
has been implemented to match the functionality of the system.

More recent incarnations of these programs can be found in my Canvas
and Overdub repositories.
