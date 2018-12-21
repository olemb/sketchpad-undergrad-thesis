#include <stdio.h>
#include <stdlib.h>

#include "wave.h"
#include "record.h"

#define MAX_SHORT 32767
#define MIN_SHORT -32768

struct segment *top = NULL;
struct segment *segments;
struct segment total;
struct segment used;
static struct segment used_backup;  // Backed up before recording

short *wet;
short *dry;

int mode = STOPPED;

long pos = 0;
float input_peak = 0.0f;
float output_peak = 0.0f;

int monitor_input = 0;
int half_speed = 0;

static void peak_meter_update(float *peak, int current)
{
  float c;
  if(*peak > 0)
    (*peak) -= (0.4f/SAMPLE_RATE);
  current = abs(current);
  c = (float)current / MAX_SHORT;
  if(c > *peak)
    *peak = c;
}

static long clip_sample(long sample)
{
  if(sample > MAX_SHORT)
    sample = MAX_SHORT;
  else if(sample < MIN_SHORT)
    sample = MIN_SHORT;

  return sample;
}

static void new_layer(void)
{
  top = calloc(1, sizeof(struct segment));
  used_backup = used;  // Back up in case of undo
  top->level = 1.0f;
}

static void keep_layer(void)
{
  if(top) {
    top->next = segments;
    segments = top;
    top = NULL;
  }
}

static void discard_layer(void)
{
  if(top) {
    free(top);
    top = NULL;
    used = used_backup;  // Let's get the old values back
  }
}

static void store_sample(int n)
{
  struct segment *this;

  if(segments != NULL && segments->start == n) {
    this = segments;
    dry[n] = clip_sample(dry[n]+(wet[n]*this->level));
    wet[n] = 0;
    this->start++;
    if(this->start == this->end) {
      segments = this->next;
      free(this);
    }
  }
}

static void prepare(int n)
{
  store_sample(n);
  if(n >= used.end) {
    dry[pos] = wet[pos] = 0;  // Could allocate memory here
  }
}

int real_process_sample(int input)
{
  int output = 0;

  if(mode & STATE_RUNNING && pos < total.end) {
    prepare(pos);
    output += dry[pos];

    if(mode & STATE_RECORDING) {
      wet[pos] = input;
      top->end++;
      if(used.end == pos)
	used.end++;
    } else {
      if(top) {
	output += (wet[pos] * top->level);
      }
    }
    pos++;
  }

  peak_meter_update(&input_peak, input);
  peak_meter_update(&output_peak, output+input);
  // peak_meter_update(&output_peak, output);

  if(monitor_input)
    output += input;

  return clip_sample(output);
}

int process_sample(int input)
{
  static int i = 0;
  int val[2] = {0, 0};
  int output;

  // This half speed wrapper only works with stereo
  if(half_speed) {
    if(i < 2)
      val[i] = real_process_sample(input);
    output = val[i%2];
    i++;
    i %= 4;
  } else {
    output = real_process_sample(input);
  }

  return output;
}

void switch_mode(int new_mode)
{
  if(mode == RECORDING) {
    if(top != NULL)
      top->end = pos;
  }

  if(new_mode == RECORDING) {
    keep_layer();
    new_layer();
  }

  pos = 0;
  mode = new_mode;
}

void undo(void)
{
  discard_layer();
  switch_mode(STOPPED);
}

static void alloc_buffers(long nsamples)
{
  wet = malloc(nsamples * sizeof(short));
  dry = malloc(nsamples * sizeof(short));
}

void init(int secs)
{
  int nsamples = (secs * SAMPLE_RATE * NUM_CHANNELS);

  alloc_buffers(nsamples);
  used.start = used.end = 0;
  total.start = 0;
  total.end = nsamples;
}

void clear(void)
{
  struct segment *this;

  if(top) {
    free(top);
    top = NULL;
  }
  while(segments) {
    this = segments;
    segments = this->next;
    free(this);
  }

  used.start = used.end = 0;
}

void cleanup(void)
{
  free(dry);
  free(wet);
}

int load_recording(char *filename)
{
  int ret;
  
  ret = wave_read(filename, (char *)dry, total.end*sizeof(short));
  if(ret != -1) {
    used.start = 0;
    used.end = ret/sizeof(short);
  }
  return ret;
}

int save_recording(char *filename)
{
  FILE *file;
  int i;
  short sample;

  short *buf;
  //int bufsize = 44100 * 2 * 0.1;  // One second
  int bufsize = 4000;

  buf = malloc(bufsize*sizeof(sample));

  file = wave_open(filename);
  if(!file)
    return -1;
  
  for(i = 0; i < used.end; i++) {
    prepare(i);
    
    sample = dry[i];
    if(top)
      sample += (wet[i] * top->level);
    sample = clip_sample(sample);
    
    //fwrite(&sample, sizeof(sample), 1, file);

    // Flush buffer
    if(i > 0 && (i % bufsize) == 0)
      fwrite(buf, sizeof(sample), bufsize, file);
    buf[i % bufsize] = sample;
  }
  if(i % bufsize)
    fwrite(buf, sizeof(sample), i % bufsize, file);

  wave_close(file);

  return 0;
}

int save_top_layer(char *filename)
{
  if(top)
    return wave_write(filename, (char *)wet, top->end*sizeof(short));
  return 0;
  // Should also save the level somewhere
}
