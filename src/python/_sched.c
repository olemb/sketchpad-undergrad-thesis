/*
  Python wrappers for sched_setscheduler() and mlockall().  These are
  not full wrappers. They only expose the functionality needed by the
  recording application.
 */

#include <stdio.h>
#include <stdlib.h>
#include <Python.h>
#include <sys/mman.h>
#include <sched.h>

static PyObject *func_realtime(PyObject *self, PyObject *args)
{
  struct sched_param p;
	
  if(!PyArg_ParseTuple(args, "i", &p.sched_priority)) {
    return NULL;
  }

  if(sched_setscheduler(0, SCHED_FIFO, &p) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *func_mlockall(PyObject *self, PyObject *args)
{
  struct sched_param p;
  p.sched_priority = 98;

  if(!PyArg_ParseTuple(args, "")) {
    return NULL;
  }

  if(mlockall(MCL_CURRENT|MCL_FUTURE) < 0)  // Lock all pages
    return NULL;
	  
  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef methods[] = {
  {"realtime",  func_realtime, METH_VARARGS},
  {"mlockall",  func_mlockall, METH_VARARGS},
  {NULL, NULL}        /* Sentinel */
};


void init_sched()
{
  (void) Py_InitModule("_sched", methods);
}
