/* This probably belongs in record.c */

#include <pthread.h>

static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void acquire_lock(void)
{
  pthread_mutex_lock(&mutex);
}

void release_lock(void)
{
  pthread_mutex_unlock(&mutex);
}
