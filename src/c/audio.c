#include <linux/soundcard.h>
#include <pthread.h>
#include <sys/poll.h>
#include <stdlib.h> 
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <stdio.h>

#include "lock.h"
#include "record.h"

/*******************************************************************
 * Audio
 *
 * See http://www.4front-tech.com/pguide/audio.html
 */

static int dsp;
static pthread_t thread;
static int iobufsize;
static int audio_paused = 0;

char audio_errmsg[100];

#define FAIL(msg) { sprintf(audio_errmsg, "%s", msg); return -1; }

static volatile int done = 0;

static void *audio_thread(void *arg)
{
  int nsamples = iobufsize / sizeof(short);
  int i;
  short *in;
  short *out;
  struct pollfd pf = { dsp, POLLOUT, 0 };

  /* Error checking here */
  in = (short *)calloc(sizeof(short), nsamples);
  out = (short *)calloc(sizeof(short), nsamples);

  write(dsp, out, iobufsize);  // Write if there's room

  while(!done) {
    if(audio_paused) {
      // Wait for condition
    } else {
      read(dsp, in, iobufsize);  // Blocking read
      
      acquire_lock();
      for(i = 0; i < nsamples; i++) {
	out[i] = process_sample(in[i]);
      }
      release_lock();
      
      if(1 == poll(&pf, 1, 0)) {
	write(dsp, out, iobufsize);  // Write if there's room
      }
    }
  }

  return NULL;
}

int audio_start(void)
{ 
  int arg;

  done = 0;

  dsp = open("/dev/dsp", O_RDWR);
  if(dsp == -1) {
    FAIL("Error opening /dev/dsp");
  } else {

    if(ioctl(dsp, SNDCTL_DSP_SETDUPLEX, 0))  // Before DSP_CAP_DUPLEX
      FAIL("Unable to set full duplex mode");

    arg = 0x0003000B;
    arg = 0x0003000A;  // Cause occational overruns in multiuser mode
    //arg = 0x00030009;  // Works in single user mode, with perceptable latency
    //arg = 0x00030008;  // Causes recording overruns in single user mode
    if(ioctl(dsp,SNDCTL_DSP_SETFRAGMENT, &arg) == -1) {
      FAIL("Unable to set fragment size\n");
    }

    arg = 1;
    if(ioctl(dsp, SNDCTL_DSP_STEREO, &arg) == -1)
      FAIL("Unable to set stereo");

    arg = AFMT_S16_NE;
    if(ioctl(dsp, SNDCTL_DSP_SAMPLESIZE, &arg) == -1)
      FAIL("Unable to set sample format");
    if(arg != AFMT_S16_NE)
      FAIL("Sample format not supported");\

    arg = SAMPLE_RATE;
    if(ioctl(dsp, SNDCTL_DSP_SPEED, &arg) == -1)
      FAIL("Unable to set sample rate");
    //printf("%dHz\n", arg);

    ioctl(dsp, SNDCTL_DSP_GETBLKSIZE, &iobufsize);
    //printf("Block size: %d\n", arg);

#ifdef NONBLOCK_AUDIO
    fcntl(dsp, F_SETFL, O_NONBLOCK);
#endif
  }

  audio_paused = 0;
  done = 0;

  /* Error checking here */
  pthread_create(&thread, NULL, audio_thread, NULL);

  return 0;
}

void audio_stop(void)
{
  void *ret;
  
  acquire_lock();  // It it necessary to lock here?
  done = 1;        // Tell the audio thread to exit
  release_lock();
  pthread_join(thread, &ret);

  ioctl(dsp, SNDCTL_DSP_RESET, 0);  // Stop audio immediately

  close(dsp);
}

/*
 * These will be replaced with proper audio pause/resume
 */
int audio_pause(void)
{
  audio_stop();
  return 0;


  if(audio_paused) {
    return 0;
  }

  acquire_lock();  // It it necessary to lock here?
  audio_paused = 1;
  acquire_lock();

  // Pause input
  if(ioctl(dsp, SNDCTL_DSP_RESET, 0) == -1)
    FAIL("Unable to pause audio");
  // Pause output
  if(ioctl(dsp, SNDCTL_DSP_POST, 0) == -1)
    FAIL("Unable to pause audio");
  return 0;
}

int audio_resume(void)
{
  audio_start();
  return 0;

  acquire_lock();
  audio_paused = 0;
  acquire_lock();

  //audio_start();
  return 0;
}
