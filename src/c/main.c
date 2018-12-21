#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "record.h"
#include "audio.h"
#include "getkey.h"
#include "lock.h"

static char *mode_name = "stopped";

long convert_pos(long value)
{
  return value / SAMPLE_RATE / NUM_CHANNELS;
}

static void update_display()
{
  static char old[80] = {'\0'};
  char display[80];
  int i;
  char peak_meter[30];
  int peak_meter_size = 20;
  int peak;

  peak = (int)(output_peak * peak_meter_size);
  for(i = 0; i < peak && i < peak_meter_size; i++)
    peak_meter[i] = '|';
  for(i = peak; i < peak_meter_size; i++)
    peak_meter[i] = ' ';
  peak_meter[peak_meter_size] = '\0';

  if(output_peak >= 1.0) {
    peak_meter[peak_meter_size-1] = '*';
  }

  // "level=%.2f%s"
  sprintf(display, "[%s] %s %ld of %ld (%ld free) %s%s",
	  //input_meter,
	  peak_meter,
	  mode_name,
	  convert_pos(pos),
	  convert_pos(used.end),
	  convert_pos(total.end-used.end),
          // top ? top->level : 1.0f,
	  // top ? " top" : "",
	  half_speed ? " (half speed)" : "",
	  monitor_input ? " (monitor)" : "");
  
  //printf("'%s' '%s'\n", old, display);

  if(strcmp(display, old)) {
    printf("\r%s", display);
    for(i = 77-strlen(display); i > 0; i--)
      putchar(' ');
    fflush(stdout);
    strcpy(old, display);
  }
}

int main(int argc, char *argv[])
{
  int c;
  int done = 0;
  char *filename;

  if(argc < 2)
    filename = "/tmp/test.wav";
  else
    filename = argv[1];

  init(10*60);
  //load_recording(filename);
  audio_start();

  while(!done) {
    c = getkey(100);

    acquire_lock();
    switch(c) {
    case 0:
      // Timeout
      break;
    case 'q':
      done = 1;
      break;
    case 'b':
      switch_mode(RECORDING);
      mode_name = "recording";
      break;
    case 'n':
      switch_mode(PLAYING);
      mode_name = "playing";
      break;
    case ' ':
      switch_mode(STOPPED);
      mode_name = "stopped";
      break;
    case 127:
      undo();
      break;
    case 'm':
      monitor_input = !monitor_input;
      break;
    case 'h':
      half_speed = !half_speed;
      break;
    case 'z':
      if(top) {
	top->level -= 0.1f;
	if(top->level < 0.0f)
	  top->level = 0.0f;
      }
      break;
    case 'x':
      if(top) {
	top->level += 0.1f;
      }
      break;

    default:
      //printf("Unknown key %d\n", c);
      break;
    }
    update_display();
    release_lock();
  }

  audio_stop();
  printf("\nWriting %ld samples to %s ... \n", used.end, filename);
  fflush(stdout);
  save_recording(filename);
  puts("done");
  cleanup();

  return 0;
}
