#include <stdio.h>
#include <stdlib.h>
#include <termios.h>
#include <sys/poll.h>

static struct termios savemodes;
static int getkey_initialized = 0;

static void getkey_cleanup(void)
{
  tcsetattr(0, 0, &savemodes);
}

static void getkey_init(void)
{
  struct termios modes;
  tcgetattr(0, &modes);
  savemodes = modes;
  modes.c_lflag &= ~(ICANON|ECHO);
  tcsetattr(0, 0, &modes);
  
  atexit(getkey_cleanup);
  
  getkey_initialized = 1;
}

/*
  Returns a character, 0 on timeout, or < 0 or error.
 */
int getkey(int timeout)
{
  struct pollfd pf = { 0, POLLIN, 0 };
  int ret;

  if(!getkey_initialized)
    getkey_init();

  ret = poll(&pf, 1, timeout);
  if(ret > 0)
    ret = getchar();

  return ret;
}
