#ifndef __RECORD_H__
#define __RECORD_H__

// API

#define SAMPLE_RATE 44100  /* Should probably not be a constant */
#define NUM_CHANNELS 2

struct segment {
  struct segment *next;
  long start;
  long end;
  float level;  // Mix level for layer. 0 for recorded level.
};

#define STATE_RUNNING   0x1
#define STATE_RECORDING 0x2

#define STOPPED   (0)
#define PLAYING   (STATE_RUNNING)
#define RECORDING (STATE_RUNNING | STATE_RECORDING)

extern struct segment *top;
extern struct segment *segments;
extern struct segment total;
extern struct segment used;

// Sample buffers
extern short *wet;
extern short *dry;

extern int mode;

extern long pos;
extern float input_peak;
extern float output_peak;

extern int monitor_input;
extern int half_speed;

void switch_mode(int new_mode);
void undo(void);
void clear(void);

void init(int secs);
void init_mmap(int secs, char *wet_filename, char *dry_filename);
void cleanup(void);

int load_recording(char *filename);
int save_recording(char *filename);
int save_top_layer(char *filename);

// Called by the audio thread
int process_sample(int input);


#endif
