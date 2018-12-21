#ifndef __WAVE_H__
#define __WAVE_H__

struct wave_header {
  long dunno1;
  long filesize;
  long dunno2[8];
  long datasize;
};

void wave_header_init(struct wave_header *header, long datasize);
int wave_read(char *filename, char *buf, long bufsize);
int wave_write(char *filename, char *buf, long size);

FILE *wave_open(char *filename);
void wave_close(FILE *file);


#endif
