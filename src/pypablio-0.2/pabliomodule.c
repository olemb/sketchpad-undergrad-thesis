/*
  A Python wrapper for pablio (portaudio blocking API).

  Author: Ole Martin Bjoerndalen <olemb@stud.cs.uit.no>
  URL: http://www.cs.uit.no/~olemb/software/pyportaudio/
  Version: 0.2 

  Todo:

  - be compatible with wave/aifc modules or have keyword arguments and attributes?
  - sampwidth or format (paInt16...)
  - options (sample rate, format ...)
  - can CloseAudioStream() fail?
  - should the variable be named latency or min_latency_msec?
  - return 0 or None when PA_MIN_LATENCY_MSEC is not set?
  - fileobject.c uses assert() (in open_the_file())
  - r+ and w+ or rw?
  - pablio writes some stuff to stdout:
      PA_MIN_LATENCY_MSEC = 20
      PA_MIN_LATENCY_MSEC = 20
      PortAudio: only superuser can use real-time priority.
    Is there any way to make it shut up?
  - opening two write streams (mode="w") hangs PABLIO.
    This is a bug in OpenAudioStream(). See below.
  - HostError is not a very good error message (in open())
  - handle errors in readframes() and writeframes()
  - pause() and resume() methods (close and reopen stream)?
  - should getminlatency() return seconds or milliseconds?
  - should getminlatency() be an attribute of the module?
  - check out PyMem_Free()/PyMem_Alloc()
  - check out PyString_FromFormat()

  Maybe:

  - open()/close() methods (like file object)?
  - complain if an uneven number of frames are passed to writeframes()?
  - add mode attribute or getmode() method?


  Bug in OpenAudioStream():

  // This locks PABLIO
  err = OpenAudioStream(&astream, 44100, paInt16, PABLIO_WRITE);
  printf("err=%d\n", err);
  err = OpenAudioStream(&astream, 44100, paInt16, PABLIO_WRITE);
  printf("err=%d\n", err);

  // While this works (the second call returns an error  err = OpenAudioStream(&astream, 44100, paInt16, PABLIO_READ);
  printf("err=%d\n", err);
  err = OpenAudioStream(&astream, 44100, paInt16, PABLIO_READ);
  printf("err=%d\n", err);
 */

#define debug(x) ;

#if 0
static PyMemberDef file_memberlist[] = {
        {"softspace",   T_INT,          OFF(f_softspace), 0,
         "flag indicating that a space needs to be printed; used by print"},
        {"mode",        T_OBJECT,       OFF(f_mode),    RO,
         "file mode ('r', 'w', 'a', possibly with 'b' or '+' added)"},
        {"name",        T_OBJECT,       OFF(f_name),    RO,
         "file name"},
        /* getattr(f, "closed") is implemented without this table */
        {NULL}  /* Sentinel */
};
#endif

#include <Python.h>

#include "pablio.h"

#define BUF(v) PyString_AS_STRING((PyStringObject *)v)
//#define BYTES_PER_FRAME 4  // Hardcoded for now
#define RETURN_NONE return (Py_INCREF(Py_None), Py_None);

#define CLOSED_CHECK(obj) \
 {if((obj)->astream == NULL) { \
  PyErr_SetString(PyExc_ValueError, "I/O operation on closed audiostream"); \
  return NULL; }}

char audiostream__doc__[] = "\
An audiostream object";

typedef struct {
  PyObject_HEAD
  PABLIO_Stream *astream;
  int flags;
  int latency;
  int frame_size;
} audiostream;

/* Audiostream type */
extern PyTypeObject audiostream_type;
#if 0  /* Doesn't work for some reason */
staticforward PyTypeObject audiostream_type;
#endif

/* constructor */
static PyObject *audiostream_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  // Todo: Should I do something else here? (like fileobject.c/file_new())

  PyObject *self;

  debug("[audiostream_new() called)\n");
  self = type->tp_alloc(type, 0);
  debug("... alloc returned\n");
  return self;
}

static int get_frame_size(int format, int flags)
{
  int ret;

  ret = Pa_GetSampleSize(format);
  if(flags & PABLIO_STEREO)
    ret *= 2;

  return ret;
}

static int audiostream_init(PyObject *self, PyObject *args, PyObject *kwds)
{
  audiostream *object = (audiostream *)self;
  char *mode = "r";
  int rate = 44100;  /* Todo: these should be settable */
  int format = paInt16;
  int stereo = 1;
  static PABLIO_Stream *astream;
  char *str;
  int err;
  int ret = 0;
  int flags = 0;
  static char *kwlist[] = {"mode", "framerate", "format", "stereo", NULL};

  debug("[audiostream_init() called)\n");

  if(!PyArg_ParseTupleAndKeywords(args, kwds, "|siii", kwlist, &mode, &rate, &format, &stereo)) {
    return -1;
  }

  if(strcmp(mode, "r") == 0)
    flags |= PABLIO_READ;
  else if(strcmp(mode, "w") == 0)
    flags |= PABLIO_WRITE;
  else if(strcmp(mode, "r+") == 0)
    flags |= PABLIO_READ_WRITE;
  else if(strcmp(mode, "w+") == 0)
    flags |= PABLIO_READ_WRITE;

  if(stereo)
    flags |= PABLIO_STEREO;
  else
    flags |= PABLIO_MONO;

  //printf("rate=%d format=%d stereo=%d\n", rate, format, stereo);

  err = OpenAudioStream(&astream, rate, format, flags);
  if(err != paNoError) {
    PyErr_SetString(PyExc_IOError, Pa_GetErrorText(err));
    return -1;
  }

  // Initialize the object
  object->astream = astream;
  object->flags = flags;
  object->frame_size = get_frame_size(format, flags);  // Todo: handle paCustomFormat

  printf("frame_size: %d\n", object->frame_size);

  str = getenv("PA_MIN_LATENCY_MSEC");
  if(str != NULL)
    object->latency = atoi(str);
  else
    object->latency = -1;

  //debug("%x %x %x %x\n", object->flags, PABLIO_READ, PABLIO_WRITE, PABLIO_READ_WRITE);

  return ret;
}

static void audiostream_dealloc(PyObject *self)
{
  audiostream *object = (audiostream *)self;

  debug("[audiostream_dealloc() called]\n");

  // Todo: can this fail?
  if(object->astream != NULL) {
    debug("  [dealloc() closing stream]\n");
    CloseAudioStream(object->astream);
    object->astream = NULL;
  }
  
  object->ob_type->tp_free((PyObject *)object);
}

static char audiostream_readframes__doc__[] = "\
  Read n frames from the stream.\n\
  Will not return until all the data has been read.";

static PyObject *audiostream_readframes(PyObject *self, PyObject *args)
{
  audiostream *object = (audiostream *)self;
  int nframes;
  PyObject *str;
  int err;

  CLOSED_CHECK(object);

  if((object->flags & PABLIO_READ) == 0) {
    PyErr_SetString(PyExc_TypeError, "audio stream is write only");
    return NULL;
  }

  if(!PyArg_ParseTuple(args, "i", &nframes)) {
    return NULL;
  }

  str = PyString_FromStringAndSize((char *)NULL, nframes*object->frame_size);
  Py_BEGIN_ALLOW_THREADS;
  err = ReadAudioStream(object->astream, BUF(str), nframes);
  Py_END_ALLOW_THREADS;

  // Todo: handle error

  return str;
}

static char audiostream_writeframes__doc__[] = "\
Write data to the stream.\n\
Will not return until all the data has been written.";

static PyObject *audiostream_writeframes(PyObject *self, PyObject *args)
{
  audiostream *object = (audiostream *)self;
  char *buf;
  int nbytes;
  int err;

  CLOSED_CHECK(object);

  if((object->flags & PABLIO_WRITE) == 0) {
    PyErr_SetString(PyExc_TypeError, "audio stream is read only");
    return NULL;
  }

  if(!PyArg_ParseTuple(args, "t#", &buf, &nbytes)) {
    return NULL;
  }

  Py_BEGIN_ALLOW_THREADS;
  err = WriteAudioStream(object->astream, buf, nbytes/object->frame_size);
  Py_END_ALLOW_THREADS;

  // Todo: handle error

  RETURN_NONE;
}

static PyObject *audiostream_getreadable(PyObject *self, void *var)
{
  audiostream *object = (audiostream *)self;

  CLOSED_CHECK(object);

  return PyInt_FromLong(GetAudioStreamReadable(object->astream));
}

static PyObject *audiostream_getwriteable(PyObject *self, void *var)
{
  audiostream *object = (audiostream *)self;

  CLOSED_CHECK(object);

  return PyInt_FromLong(GetAudioStreamWriteable(object->astream));
}

static PyObject *audiostream_getminlatency(PyObject *self, void *var)
{
  audiostream *object = (audiostream *)self;

  if(object->latency == -1)
    return PyInt_FromLong(0);  // or return PyNone?
  else
    return PyFloat_FromDouble(object->latency / 1000.0);
}

static char audiostream_close__doc__[] = "\
Close the audio stream.";

static PyObject *audiostream_close(PyObject *self, PyObject *args)
{
  audiostream *object = (audiostream *)self;

  if(object->astream != NULL) {
    debug("  [close() closing stream]\n");
    CloseAudioStream(object->astream);
    object->astream = NULL;
  }

  RETURN_NONE;
}

static PyObject *audiostream_getclosed(PyObject *self, PyObject *args)
{
  audiostream *object = (audiostream *)self;

  return PyInt_FromLong((long)(object->astream == NULL));
}

PyMethodDef audiostream_methods[] = {
  {"readframes", (PyCFunction)audiostream_readframes, METH_VARARGS, audiostream_readframes__doc__},
  {"writeframes", (PyCFunction)audiostream_writeframes, METH_VARARGS, audiostream_writeframes__doc__},
  {"close", (PyCFunction)audiostream_close, METH_NOARGS, audiostream_close__doc__},
  {NULL, NULL, 0, NULL},
};

static PyGetSetDef audiostream_getsetlist[] = {
  {"readable", (getter)audiostream_getreadable, NULL, "the number of frames that can be read without blocking"},
  {"writeable", (getter)audiostream_getwriteable, NULL, "the number of frame that can be written without blocking"},
  {"minlatency", (getter)audiostream_getminlatency, NULL, "minimum latency in seconds (or 0 if PA_MIN_LATENCY_MSEC is not set)"},
  {"closed", (getter)audiostream_getclosed, NULL, "flag set if the audiostream is closed"},
  {NULL, NULL, 0, NULL},
};

PyTypeObject audiostream_type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,
  "audiostream",                /* char *tp_name; */
  sizeof(audiostream),          /* int tp_basicsize; */
  0,                        /* int tp_itemsize;   not used much */
  audiostream_dealloc,          /* destructor tp_dealloc; */
  0, // audiostream_print,            /* printfunc  tp_print;   */
  0, // audiostream_getattr,          /* getattrfunc  tp_getattr;  __getattr__ */
  0, // audiostream_setattr,          /* setattrfunc  tp_setattr;  __setattr__ */
  0, // audiostream_compare,          /* cmpfunc  tp_compare;  __cmp__ */
  0, // audiostream_repr,             /* reprfunc  tp_repr;    __repr__ */
  0, // &audiostream_as_number,       /* PyNumberMethods *tp_as_number; */
  0,                        /* PySequenceMethods *tp_as_sequence; */
  0,                        /* PyMappingMethods *tp_as_mapping; */
  0, // audiostream_hash              /* hashfunc tp_hash;      __hash__ */
  0,                        /* ternaryfunc tp_call;   __call__ */
  0, // audiostream_repr,              /* reprfunc tp_str;       __str__ */
  0,                   /* tp_getattro */
  0,                   /* tp_setattro */
  0,                   /* tp_as_buffer */
  0,                   /* tp_xxx4 */
  audiostream__doc__,      /* tp_doc */
  0,                                      /* tp_traverse */
  0,                                      /* tp_clear */
  0,                                      /* tp_richcompare */
  0,                                      /* tp_weaklistoffset */
  0, //file_getiter,                           /* tp_iter */
  0,                                      /* tp_iternext */
  audiostream_methods,                           /* tp_methods */
  0, // file_memberlist,                        /* tp_members */
  audiostream_getsetlist,                        /* tp_getset */
  0,                                      /* tp_base */
  0,                                      /* tp_dict */
  0,                                      /* tp_descr_get */
  0,                                      /* tp_descr_set */
  0,                                      /* tp_dictoffset */
  (initproc)audiostream_init,                    /* tp_init */
  PyType_GenericAlloc,                    /* tp_alloc */
  audiostream_new,                               /* tp_new */
  _PyObject_Del,                          /* tp_free */
};

PyMethodDef methods[] = {
  {NULL, NULL, 0, NULL}
};

/* Convenience routine to export an integer value.
 * (Borrowed from the socket module.)
 *
 * Errors are silently ignored, for better or for worse...
 */
static void
insint(PyObject *d, char *name, int value)
{
        PyObject *v = PyInt_FromLong((long) value);
        if (!v || PyDict_SetItemString(d, name, v))
                PyErr_Clear();

        Py_XDECREF(v);
}

void initpablio(void)
{
  PyObject *mod, *dict;

  mod = Py_InitModule3("pablio", methods, "python wrapper for pablio");
  if(mod == NULL)
    return;

  if (PyType_Ready(&audiostream_type) < 0)
    return;

  dict = PyModule_GetDict(mod);
  if(dict == NULL)
    return;

  insint(dict, "paFloat32", paFloat32);
  insint(dict, "paInt16", paInt16);
  insint(dict, "paInt32", paInt32);
  insint(dict, "paInt24", paInt24);
  insint(dict, "paPackedInt24", paPackedInt24);
  insint(dict, "paInt8", paInt8);
  insint(dict, "paUInt8", paUInt8);
  insint(dict, "paCustomFormat", paCustomFormat);

  insint(dict, "PABLIO_STEREO", PABLIO_STEREO);
  insint(dict, "PABLIO_MONO", PABLIO_MONO);
  insint(dict, "PABLIO_READ", PABLIO_READ);
  insint(dict, "PABLIO_WRITE", PABLIO_WRITE);
  insint(dict, "PABLIO_READ_WRITE", PABLIO_READ_WRITE);

  Py_INCREF(&audiostream_type);
  if (PyDict_SetItemString(dict, "open", (PyObject *)&audiostream_type) < 0)
    return;
}
