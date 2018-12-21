import sys
from distutils.core import setup, Extension

DESCRIPTION = """pypablio is a python wrapper for PABLIO, portaudio's
blocking API."""

padir = "portaudio_v18/"

#
# Common portaudio files
#
pa_sources = [
    padir + "pa_common/pa_convert.c",
    padir + "pa_common/pa_lib.c",
    padir + "pa_common/pa_trace.c",
    padir + "pablio/pablio.c",
    padir + "pablio/ringbuffer.c"]
include_dirs = [padir + "pa_common", padir + "pablio"]
libraries = []

#
# System specific portaudio files
#
if sys.platform == 'win32':
    pa_sources.append(padir + "pa_win_wmme/pa_win_wmme.c")
    include_dirs.append(padir + "pa_win_wmme")
    libraries.append("winmm")
elif sys.platform == 'linux2':
    pa_sources.append(padir + "pa_unix_oss/pa_unix_oss.c")

#
# DirectSound (Not tested, since it turned out I didn't have
# DirectSound after all.)
#
if 0:
    pa_sources.append(padir + "pa_win_ds/pa_dsound.c")
    pa_sources.append(padir + "pa_win_ds/dsound_wrapper.c")
    include_dirs.append(padir + "pa_win_ds")
    
setup(ext_modules=[Extension("pablio",
                             ["pabliomodule.c"] + pa_sources,
                             libraries=libraries,
                             include_dirs=include_dirs)],

      name='pypablio',
      version='0.2',
      license='MIT',
      url='http://www.cs.uit.no/~olemb/',
      author='Ole Martin Bjorndalen',
      author_email='olemb@stud.cs.uit.no',
      description='Python wrapper for the PABLIO audio API',
      long_description=DESCRIPTION)
