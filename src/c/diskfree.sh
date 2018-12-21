#!/bin/sh

df -k /tmp | awk 'NR==2 {printf("%d seconds free\n", $4/((44100*4/1024)));}'
