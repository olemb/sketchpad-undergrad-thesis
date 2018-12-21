#ifndef __AUDIO_H__
#define __AUDIO_H__

int audio_start(void);
void audio_stop(void);
int audio_pause(void);
int audio_resume(void);

extern char audio_errmsg[];

#endif
