#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include "wave.h"

/* OK, I admit it: This is a bit dirty. :D */
static char default_wave_header[] = {
  0x52, 0x49 ,0x46, 0x46,
  0x99, 0x99, 0x99, 0x99,  /* file size (data + header) */
  0x57, 0x41, 0x56, 0x45,
  0x66, 0x6d, 0x74, 0x20, 
  0x10, 0x00, 0x00, 0x00,
  0x01, 0x00, 0x02, 0x00,
  0x44, 0xac, 0x00, 0x00,
  0x10, 0xb1, 0x02, 0x00,
  0x04, 0x00, 0x10, 0x00,
  0x64, 0x61, 0x74, 0x61,
  0x99, 0x99, 0x99, 0x99   /* data size */
};

void wave_header_init(struct wave_header *header, long datasize)
{
  memcpy(header, default_wave_header, sizeof(struct wave_header));
  header->filesize = datasize + sizeof(header);
  header->datasize = datasize;
}

int wave_read(char *filename, char *buf, long bufsize)
{
  /* Should warn the user if the song is too long to fit in memory.  */
  FILE *file;
  int size = -1;

  file = fopen(filename, "r");
  if(file) {
    fflush(stdout);
    size = fseek(file, sizeof(struct wave_header), SEEK_SET);
    size = fread(buf, 1, bufsize, file);
  } else {
    size = -1;
  }

  return size;
}

FILE *wave_open(char *filename)
{
  FILE *file;
  struct wave_header header;
  // memset(&header, 0, sizeof(header));

  puts("  wave_open()");
  file = fopen(filename, "w");
  if(file) { 
    if(fwrite(&header, sizeof(struct wave_header), 1, file) != 1) {
      perror("wave_write() (header)");
      fclose(file);
      return NULL;
    }
  }

  return file;
}

void wave_close(FILE *file)
{
  struct wave_header header;
  long pos;
  puts("  wave_close()");
  pos = ftell(file);
  wave_header_init(&header, pos - sizeof(header));
  fseek(file, 0, SEEK_SET);
  if(fwrite(&header, sizeof(struct wave_header), 1, file) != 1) {
    perror("wave_write() (header)");
  }
  fclose(file);
}

int wave_write(char *filename, char *buf, long size)
{
  FILE *file;
  struct wave_header header;
  long ret;

  wave_header_init(&header, size);
  puts("wave_write() start");
  file = fopen(filename, "w");
  if(file) {
    fflush(stdout);
    if(fwrite(&header, sizeof(struct wave_header), 1, file) != 1) {
      perror("wave_write() (header)");
      return -1;
    }
    ret = fwrite(buf, 1, size, file);
    if(ret != size) {
      if(ret < 0)
	perror("wave_write() (buffer)");
      fprintf(stderr, "Wrote %ld of %ld bytes\n", ret, size);
      return -1;
    }
  } else {
    perror("wave_write() (open())");
    return -1;
  }
  puts("wave_write() stop");
  return 0;
}
