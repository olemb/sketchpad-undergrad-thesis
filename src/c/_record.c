#include <stdio.h>
#include <Python.h>

#include "record.h"
#include "audio.h"
#include "lock.h"

static PyObject *func_switch_mode(PyObject *self, PyObject *args)
{
  long new_mode;

  if (!PyArg_ParseTuple(args, "i", &new_mode))
    return NULL;

  acquire_lock();
  switch_mode(new_mode);
  release_lock();

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *func_undo(PyObject *self, PyObject *args)
{
  acquire_lock();
  undo();
  release_lock();
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *func_clear(PyObject *self, PyObject *args)
{
  acquire_lock();
  clear();
  release_lock();

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *func_set_monitor_input(PyObject *self, PyObject *args)
{
  long arg;

  if (!PyArg_ParseTuple(args, "i", &arg))
    return NULL;

  acquire_lock();
  monitor_input = arg;
  release_lock();

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *func_set_half_speed(PyObject *self, PyObject *args)
{
  long arg;

  if (!PyArg_ParseTuple(args, "i", &arg))
    return NULL;

  acquire_lock();
  half_speed = arg;
  release_lock();

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *func_set_top_level(PyObject *self, PyObject *args)
{
  float arg;

  if (!PyArg_ParseTuple(args, "f", &arg))
    return NULL;

  acquire_lock();
  if(top)
    top->level = arg;
  release_lock();

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *func_get_status(PyObject *self, PyObject *args)
{
  PyObject *dict = (PyObject *)PyDict_New();  // Should check return value

  //acquire_lock();
  PyDict_SetItemString(dict, "mode", Py_BuildValue("i", mode));
  PyDict_SetItemString(dict, "pos", Py_BuildValue("i", pos));
  PyDict_SetItemString(dict, "total_start", Py_BuildValue("i", total.start));
  PyDict_SetItemString(dict, "total_end", Py_BuildValue("i", total.end));
  PyDict_SetItemString(dict, "used_start", Py_BuildValue("i", used.start));
  PyDict_SetItemString(dict, "used_end", Py_BuildValue("i", used.end));

  if(top) {
    PyDict_SetItemString(dict, "top_start", Py_BuildValue("i", top->start));
    PyDict_SetItemString(dict, "top_end", Py_BuildValue("i", top->end));
    PyDict_SetItemString(dict, "top_level", Py_BuildValue("f", top->level));
  }

  PyDict_SetItemString(dict, "monitor_input", Py_BuildValue("i", monitor_input));
  PyDict_SetItemString(dict, "half_speed", Py_BuildValue("i", half_speed));

  PyDict_SetItemString(dict, "input_peak", Py_BuildValue("f", input_peak));
  PyDict_SetItemString(dict, "output_peak", Py_BuildValue("f", output_peak));
  //release_lock();

  return dict;
}

static PyObject *func_get_segments(PyObject *self, PyObject *args)
{
  PyObject *list = (PyObject *)PyList_New(0);  // Should check return values
  PyObject *tuple;
  struct segment *this;

  acquire_lock();
  for(this = segments; this; this = this->next) {
    tuple = (PyObject *)PyTuple_New(3);  // Should check return value
    PyTuple_SetItem(tuple, 0, Py_BuildValue("i", this->start));
    PyTuple_SetItem(tuple, 1, Py_BuildValue("i", this->end));
    PyTuple_SetItem(tuple, 2, Py_BuildValue("f", this->level));
    PyList_Append(list, tuple);  // Should check return value
  }
  release_lock();

  return list;
}


static PyObject *func_load_recording(PyObject *self, PyObject *args)
{
  char *filename;

  if (!PyArg_ParseTuple(args, "s", &filename))
    return NULL;
  
  load_recording(filename);

  return Py_BuildValue("i", 0);  // Should return something
}

static PyObject *func_save_recording(PyObject *self, PyObject *args)
{
  char *filename;

  if (!PyArg_ParseTuple(args, "s", &filename))
    return NULL;
  
  if(-1 == save_recording(filename)) {
    PyErr_SetFromErrno(PyExc_IOError);
    return NULL;
  }

  return Py_BuildValue("i", 0);  // Should return something
}
static PyObject *func_save_top_layer(PyObject *self, PyObject *args)
{
  char *filename;

  if (!PyArg_ParseTuple(args, "s", &filename))
    return NULL;
  
  save_top_layer(filename);

  return Py_BuildValue("i", 0);  // Should return something
}




static PyObject *func_init(PyObject *self, PyObject *args)
{
  long secs;

  if (!PyArg_ParseTuple(args, "i", &secs))
    return NULL;
  
  init(secs);

  return Py_BuildValue("i", 0);  // Should return something, or raise exception
}

static PyObject *func_cleanup(PyObject *self, PyObject *args)
{
  cleanup();

  return Py_BuildValue("i", 0);  // Should return something, or raise exception
}

static PyObject *func_audio_start(PyObject *self, PyObject *args)
{
  int ret;

  ret = audio_start();

  //
  if(ret) {
    return Py_BuildValue("s", audio_errmsg);
  } else {
    Py_INCREF(Py_None);
    return Py_None;
  }
  //
  Py_INCREF(Py_None);
  return Py_None; 
}

static PyObject *func_audio_stop(PyObject *self, PyObject *args)
{
  audio_stop();

  return Py_BuildValue("i", 0);  // Should return something, or raise exception
}

static PyObject *func_audio_pause(PyObject *self, PyObject *args)
{
  audio_pause();

  return Py_BuildValue("i", 0);  // Should return something, or raise exception
}

static PyObject *func_audio_resume(PyObject *self, PyObject *args)
{
  audio_resume();

  return Py_BuildValue("i", 0);  // Should return something, or raise exception
}

static PyMethodDef methods[] = {
  {"switch_mode",  func_switch_mode, METH_VARARGS},
  {"undo",  func_undo, METH_VARARGS},
  {"clear",  func_clear, METH_VARARGS},
  {"set_monitor_input",  func_set_monitor_input, METH_VARARGS},
  {"set_half_speed",  func_set_half_speed, METH_VARARGS},
  {"set_top_level",  func_set_top_level, METH_VARARGS},

  {"get_status",  func_get_status, METH_VARARGS},
  {"get_segments",  func_get_segments, METH_VARARGS},

  {"load_recording",  func_load_recording, METH_VARARGS},
  {"save_recording",  func_save_recording, METH_VARARGS},
  {"save_top_layer",  func_save_top_layer, METH_VARARGS},

  {"init",  func_init, METH_VARARGS},
  {"cleanup",  func_cleanup, METH_VARARGS},

  {"audio_start",  func_audio_start, METH_VARARGS},
  {"audio_stop",  func_audio_stop, METH_VARARGS},
  {"audio_pause",  func_audio_pause, METH_VARARGS},
  {"audio_resume",  func_audio_resume, METH_VARARGS},
  {NULL, NULL}        /* Sentinel */
};

void init_record()
{
  (void) Py_InitModule("_record", methods);
}
